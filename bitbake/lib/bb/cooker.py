#!/usr/bin/env python
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2003, 2004  Chris Larson
# Copyright (C) 2003, 2004  Phil Blundell
# Copyright (C) 2003 - 2005 Michael 'Mickey' Lauer
# Copyright (C) 2005        Holger Hans Peter Freyther
# Copyright (C) 2005        ROAD GmbH
# Copyright (C) 2006 - 2007 Richard Purdie
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import print_function
import sys, os, glob, os.path, re, time
import atexit
import itertools
import logging
import multiprocessing
import sre_constants
import threading
from cStringIO import StringIO
from contextlib import closing
from functools import wraps
import bb
from bb import utils, data, parse, event, cache, providers, taskdata, command, runqueue

logger      = logging.getLogger("BitBake")
collectlog  = logging.getLogger("BitBake.Collection")
buildlog    = logging.getLogger("BitBake.Build")
parselog    = logging.getLogger("BitBake.Parsing")
providerlog = logging.getLogger("BitBake.Provider")

class MultipleMatches(Exception):
    """
    Exception raised when multiple file matches are found
    """

class NothingToBuild(Exception):
    """
    Exception raised when there is nothing to build
    """

class state:
    initial, parsing, running, shutdown, stop = range(5)

#============================================================================#
# BBCooker
#============================================================================#
class BBCooker:
    """
    Manages one bitbake build run
    """

    def __init__(self, configuration, server_registration_cb):
        self.status = None
        self.appendlist = {}

        self.server_registration_cb = server_registration_cb

        self.configuration = configuration

        self.configuration.data = bb.data.init()

        bb.data.inheritFromOS(self.configuration.data)

        self.parseConfigurationFiles(self.configuration.file)

        if not self.configuration.cmd:
            self.configuration.cmd = bb.data.getVar("BB_DEFAULT_TASK", self.configuration.data, True) or "build"

        bbpkgs = bb.data.getVar('BBPKGS', self.configuration.data, True)
        if bbpkgs and len(self.configuration.pkgs_to_build) == 0:
            self.configuration.pkgs_to_build.extend(bbpkgs.split())

        self.parseCommandLine()

        #
        # Special updated configuration we use for firing events
        #
        self.configuration.event_data = bb.data.createCopy(self.configuration.data)
        bb.data.update_data(self.configuration.event_data)

        # TOSTOP must not be set or our children will hang when they output
        fd = sys.stdout.fileno()
        if os.isatty(fd):
            import termios
            tcattr = termios.tcgetattr(fd)
            if tcattr[3] & termios.TOSTOP:
                buildlog.info("The terminal had the TOSTOP bit set, clearing...")
                tcattr[3] = tcattr[3] & ~termios.TOSTOP
                termios.tcsetattr(fd, termios.TCSANOW, tcattr)

        self.command = bb.command.Command(self)
        self.state = state.initial

        self.parser = None

    def parseConfiguration(self):


        # Change nice level if we're asked to
        nice = bb.data.getVar("BB_NICE_LEVEL", self.configuration.data, True)
        if nice:
            curnice = os.nice(0)
            nice = int(nice) - curnice
            buildlog.verbose("Renice to %s " % os.nice(nice))

    def parseCommandLine(self):
        # Parse any commandline into actions
        if self.configuration.show_environment:
            self.commandlineAction = None

            if 'world' in self.configuration.pkgs_to_build:
                buildlog.error("'world' is not a valid target for --environment.")
            elif len(self.configuration.pkgs_to_build) > 1:
                buildlog.error("Only one target can be used with the --environment option.")
            elif self.configuration.buildfile and len(self.configuration.pkgs_to_build) > 0:
                buildlog.error("No target should be used with the --environment and --buildfile options.")
            elif len(self.configuration.pkgs_to_build) > 0:
                self.commandlineAction = ["showEnvironmentTarget", self.configuration.pkgs_to_build]
            else:
                self.commandlineAction = ["showEnvironment", self.configuration.buildfile]
        elif self.configuration.buildfile is not None:
            self.commandlineAction = ["buildFile", self.configuration.buildfile, self.configuration.cmd]
        elif self.configuration.revisions_changed:
            self.commandlineAction = ["compareRevisions"]
        elif self.configuration.show_versions:
            self.commandlineAction = ["showVersions"]
        elif self.configuration.parse_only:
            self.commandlineAction = ["parseFiles"]
        elif self.configuration.dot_graph:
            if self.configuration.pkgs_to_build:
                self.commandlineAction = ["generateDotGraph", self.configuration.pkgs_to_build, self.configuration.cmd]
            else:
                self.commandlineAction = None
                buildlog.error("Please specify a package name for dependency graph generation.")
        else:
            if self.configuration.pkgs_to_build:
                self.commandlineAction = ["buildTargets", self.configuration.pkgs_to_build, self.configuration.cmd]
            else:
                self.commandlineAction = None
                buildlog.error("Nothing to do.  Use 'bitbake world' to build everything, or run 'bitbake --help' for usage information.")

    def runCommands(self, server, data, abort):
        """
        Run any queued asynchronous command
        This is done by the idle handler so it runs in true context rather than
        tied to any UI.
        """

        return self.command.runAsyncCommand()

    def showVersions(self):

        # Need files parsed
        self.updateCache()

        pkg_pn = self.status.pkg_pn
        preferred_versions = {}
        latest_versions = {}

        # Sort by priority
        for pn in pkg_pn:
            (last_ver, last_file, pref_ver, pref_file) = bb.providers.findBestProvider(pn, self.configuration.data, self.status)
            preferred_versions[pn] = (pref_ver, pref_file)
            latest_versions[pn] = (last_ver, last_file)

        logger.plain("%-35s %25s %25s", "Package Name", "Latest Version", "Preferred Version")
        logger.plain("%-35s %25s %25s\n", "============", "==============", "=================")

        for p in sorted(pkg_pn):
            pref = preferred_versions[p]
            latest = latest_versions[p]

            prefstr = pref[0][0] + ":" + pref[0][1] + '-' + pref[0][2]
            lateststr = latest[0][0] + ":" + latest[0][1] + "-" + latest[0][2]

            if pref == latest:
                prefstr = ""

            logger.plain("%-35s %25s %25s", p, lateststr, prefstr)

    def showEnvironment(self, buildfile = None, pkgs_to_build = []):
        """
        Show the outer or per-package environment
        """
        fn = None
        envdata = None

        if buildfile:
            fn = self.matchFile(buildfile)
        elif len(pkgs_to_build) == 1:
            self.updateCache()

            localdata = data.createCopy(self.configuration.data)
            bb.data.update_data(localdata)
            bb.data.expandKeys(localdata)

            taskdata = bb.taskdata.TaskData(self.configuration.abort)
            taskdata.add_provider(localdata, self.status, pkgs_to_build[0])
            taskdata.add_unresolved(localdata, self.status)

            targetid = taskdata.getbuild_id(pkgs_to_build[0])
            fnid = taskdata.build_targets[targetid][0]
            fn = taskdata.fn_index[fnid]
        else:
            envdata = self.configuration.data

        if fn:
            try:
                envdata = bb.cache.Cache.loadDataFull(fn, self.get_file_appends(fn), self.configuration.data)
            except Exception, e:
                parselog.exception("Unable to read %s", fn)
                raise

        # emit variables and shell functions
        data.update_data(envdata)
        with closing(StringIO()) as env:
            data.emit_env(env, envdata, True)
            logger.plain(env.getvalue())

        # emit the metadata which isnt valid shell
        data.expandKeys(envdata)
        for e in envdata.keys():
            if data.getVarFlag( e, 'python', envdata ):
                logger.plain("\npython %s () {\n%s}\n", e, data.getVar(e, envdata, 1))

    def prepareTreeData(self, pkgs_to_build, task):
        """
        Prepare a runqueue and taskdata object for iteration over pkgs_to_build
        """
        # Need files parsed
        self.updateCache()

        # If we are told to do the None task then query the default task
        if (task == None):
            task = self.configuration.cmd

        pkgs_to_build = self.checkPackages(pkgs_to_build)

        localdata = data.createCopy(self.configuration.data)
        bb.data.update_data(localdata)
        bb.data.expandKeys(localdata)
        taskdata = bb.taskdata.TaskData(self.configuration.abort)

        runlist = []
        for k in pkgs_to_build:
            taskdata.add_provider(localdata, self.status, k)
            runlist.append([k, "do_%s" % task])
        taskdata.add_unresolved(localdata, self.status)

        rq = bb.runqueue.RunQueue(self, self.configuration.data, self.status, taskdata, runlist)
        rq.rqdata.prepare()

        return taskdata, rq

    def generateDepTreeData(self, pkgs_to_build, task):
        """
        Create a dependency tree of pkgs_to_build, returning the data.
        """
        taskdata, rq = self.prepareTreeData(pkgs_to_build, task)

        seen_fnids = []
        depend_tree = {}
        depend_tree["depends"] = {}
        depend_tree["tdepends"] = {}
        depend_tree["pn"] = {}
        depend_tree["rdepends-pn"] = {}
        depend_tree["packages"] = {}
        depend_tree["rdepends-pkg"] = {}
        depend_tree["rrecs-pkg"] = {}

        for task in xrange(len(rq.rqdata.runq_fnid)):
            taskname = rq.rqdata.runq_task[task]
            fnid = rq.rqdata.runq_fnid[task]
            fn = taskdata.fn_index[fnid]
            pn = self.status.pkg_fn[fn]
            version  = "%s:%s-%s" % self.status.pkg_pepvpr[fn]
            if pn not in depend_tree["pn"]:
                depend_tree["pn"][pn] = {}
                depend_tree["pn"][pn]["filename"] = fn
                depend_tree["pn"][pn]["version"] = version
            for dep in rq.rqdata.runq_depends[task]:
                depfn = taskdata.fn_index[rq.rqdata.runq_fnid[dep]]
                deppn = self.status.pkg_fn[depfn]
                dotname = "%s.%s" % (pn, rq.rqdata.runq_task[task])
                if not dotname in depend_tree["tdepends"]:
                    depend_tree["tdepends"][dotname] = []
                depend_tree["tdepends"][dotname].append("%s.%s" % (deppn, rq.rqdata.runq_task[dep]))
            if fnid not in seen_fnids:
                seen_fnids.append(fnid)
                packages = []

                depend_tree["depends"][pn] = []
                for dep in taskdata.depids[fnid]:
                    depend_tree["depends"][pn].append(taskdata.build_names_index[dep])

                depend_tree["rdepends-pn"][pn] = []
                for rdep in taskdata.rdepids[fnid]:
                    depend_tree["rdepends-pn"][pn].append(taskdata.run_names_index[rdep])

                rdepends = self.status.rundeps[fn]
                for package in rdepends:
                    depend_tree["rdepends-pkg"][package] = []
                    for rdepend in rdepends[package]:
                        depend_tree["rdepends-pkg"][package].append(rdepend)
                    packages.append(package)

                rrecs = self.status.runrecs[fn]
                for package in rrecs:
                    depend_tree["rrecs-pkg"][package] = []
                    for rdepend in rrecs[package]:
                        depend_tree["rrecs-pkg"][package].append(rdepend)
                    if not package in packages:
                        packages.append(package)

                for package in packages:
                    if package not in depend_tree["packages"]:
                        depend_tree["packages"][package] = {}
                        depend_tree["packages"][package]["pn"] = pn
                        depend_tree["packages"][package]["filename"] = fn
                        depend_tree["packages"][package]["version"] = version

        return depend_tree


    def generateDepTreeEvent(self, pkgs_to_build, task):
        """
        Create a task dependency graph of pkgs_to_build.
        Generate an event with the result
        """
        depgraph = self.generateDepTreeData(pkgs_to_build, task)
        bb.event.fire(bb.event.DepTreeGenerated(depgraph), self.configuration.data)

    def generateDotGraphFiles(self, pkgs_to_build, task):
        """
        Create a task dependency graph of pkgs_to_build.
        Save the result to a set of .dot files.
        """

        depgraph = self.generateDepTreeData(pkgs_to_build, task)

        # Prints a flattened form of package-depends below where subpackages of a package are merged into the main pn
        depends_file = file('pn-depends.dot', 'w' )
        print("digraph depends {", file=depends_file)
        for pn in depgraph["pn"]:
            fn = depgraph["pn"][pn]["filename"]
            version = depgraph["pn"][pn]["version"]
            print('"%s" [label="%s %s\\n%s"]' % (pn, pn, version, fn), file=depends_file)
        for pn in depgraph["depends"]:
            for depend in depgraph["depends"][pn]:
                print('"%s" -> "%s"' % (pn, depend), file=depends_file)
        for pn in depgraph["rdepends-pn"]:
            for rdepend in depgraph["rdepends-pn"][pn]:
                print('"%s" -> "%s" [style=dashed]' % (pn, rdepend), file=depends_file)
        print("}", file=depends_file)
        logger.info("PN dependencies saved to 'pn-depends.dot'")

        depends_file = file('package-depends.dot', 'w' )
        print("digraph depends {", file=depends_file)
        for package in depgraph["packages"]:
            pn = depgraph["packages"][package]["pn"]
            fn = depgraph["packages"][package]["filename"]
            version = depgraph["packages"][package]["version"]
            if package == pn:
                print('"%s" [label="%s %s\\n%s"]' % (pn, pn, version, fn), file=depends_file)
            else:
                print('"%s" [label="%s(%s) %s\\n%s"]' % (package, package, pn, version, fn), file=depends_file)
            for depend in depgraph["depends"][pn]:
                print('"%s" -> "%s"' % (package, depend), file=depends_file)
        for package in depgraph["rdepends-pkg"]:
            for rdepend in depgraph["rdepends-pkg"][package]:
                print('"%s" -> "%s" [style=dashed]' % (package, rdepend), file=depends_file)
        for package in depgraph["rrecs-pkg"]:
            for rdepend in depgraph["rrecs-pkg"][package]:
                print('"%s" -> "%s" [style=dashed]' % (package, rdepend), file=depends_file)
        print("}", file=depends_file)
        logger.info("Package dependencies saved to 'package-depends.dot'")

        tdepends_file = file('task-depends.dot', 'w' )
        print("digraph depends {", file=tdepends_file)
        for task in depgraph["tdepends"]:
            (pn, taskname) = task.rsplit(".", 1)
            fn = depgraph["pn"][pn]["filename"]
            version = depgraph["pn"][pn]["version"]
            print('"%s.%s" [label="%s %s\\n%s\\n%s"]' % (pn, taskname, pn, taskname, version, fn), file=tdepends_file)
            for dep in depgraph["tdepends"][task]:
                print('"%s" -> "%s"' % (task, dep), file=tdepends_file)
        print("}", file=tdepends_file)
        logger.info("Task dependencies saved to 'task-depends.dot'")

    def buildDepgraph( self ):
        all_depends = self.status.all_depends
        pn_provides = self.status.pn_provides

        localdata = data.createCopy(self.configuration.data)
        bb.data.update_data(localdata)
        bb.data.expandKeys(localdata)

        matched = set()
        def calc_bbfile_priority(filename):
            for _, _, regex, pri in self.status.bbfile_config_priorities:
                if regex.match(filename):
                    if not regex in matched:
                        matched.add(regex)
                    return pri
            return 0

        # Handle PREFERRED_PROVIDERS
        for p in (bb.data.getVar('PREFERRED_PROVIDERS', localdata, 1) or "").split():
            try:
                (providee, provider) = p.split(':')
            except:
                providerlog.critical("Malformed option in PREFERRED_PROVIDERS variable: %s" % p)
                continue
            if providee in self.status.preferred and self.status.preferred[providee] != provider:
                providerlog.error("conflicting preferences for %s: both %s and %s specified", providee, provider, self.status.preferred[providee])
            self.status.preferred[providee] = provider

        # Calculate priorities for each file
        for p in self.status.pkg_fn:
            self.status.bbfile_priority[p] = calc_bbfile_priority(p)

        for collection, pattern, regex, _ in self.status.bbfile_config_priorities:
            if not regex in matched:
                collectlog.warn("No bb files matched BBFILE_PATTERN_%s '%s'" % (collection, pattern))

    def findConfigFiles(self, varname):
        """
        Find config files which are appropriate values for varname.
        i.e. MACHINE, DISTRO
        """
        possible = []
        var = varname.lower()

        data = self.configuration.data
        # iterate configs
        bbpaths = bb.data.getVar('BBPATH', data, True).split(':')
        for path in bbpaths:
            confpath = os.path.join(path, "conf", var)
            if os.path.exists(confpath):
                for root, dirs, files in os.walk(confpath):
                    # get all child files, these are appropriate values
                    for f in files:
                        val, sep, end = f.rpartition('.')
                        if end == 'conf':
                            possible.append(val)

        bb.event.fire(bb.event.ConfigFilesFound(var, possible), self.configuration.data)

    def findInheritsClass(self, klass):
        """
        Find all recipes which inherit the specified class
        """
        pkg_list = []

        for pfn in self.status.pkg_fn:
            inherits = self.status.inherits.get(pfn, None)
            if inherits and inherits.count(klass) > 0:
                pkg_list.append(self.status.pkg_fn[pfn])

        return pkg_list

    def generateTargetsTreeData(self, pkgs_to_build, task):
        """
        Create a tree of pkgs_to_build metadata, returning the data.
        """
        taskdata, rq = self.prepareTreeData(pkgs_to_build, task)

        seen_fnids = []
        target_tree = {}
        target_tree["depends"] = {}
        target_tree["pn"] = {}
        target_tree["rdepends-pn"] = {}

        for task in xrange(len(rq.rqdata.runq_fnid)):
            taskname = rq.rqdata.runq_task[task]
            fnid = rq.rqdata.runq_fnid[task]
            fn = taskdata.fn_index[fnid]
            pn = self.status.pkg_fn[fn]
            version  = "%s:%s-%s" % self.status.pkg_pepvpr[fn]
            summary = self.status.summary[fn]
            license = self.status.license[fn]
            section = self.status.section[fn]
            if pn not in target_tree["pn"]:
                target_tree["pn"][pn] = {}
                target_tree["pn"][pn]["filename"] = fn
                target_tree["pn"][pn]["version"] = version
                target_tree["pn"][pn]["summary"] = summary
                target_tree["pn"][pn]["license"] = license
                target_tree["pn"][pn]["section"] = section
            if fnid not in seen_fnids:
                seen_fnids.append(fnid)
                packages = []

                target_tree["depends"][pn] = []
                for dep in taskdata.depids[fnid]:
                    target_tree["depends"][pn].append(taskdata.build_names_index[dep])

                target_tree["rdepends-pn"][pn] = []
                for rdep in taskdata.rdepids[fnid]:
                    target_tree["rdepends-pn"][pn].append(taskdata.run_names_index[rdep])

        return target_tree

    def generateTargetsTree(self, klass):
        """
        Generate a dependency tree of buildable targets
        Generate an event with the result
        """
        pkgs = ['world']
        # if inherited_class passed ensure all recipes which inherit the
        # specified class are included in pkgs
        if klass:
            extra_pkgs = self.findInheritsClass(klass)
            pkgs = pkgs + extra_pkgs

        # generate a dependency tree for all our packages
        tree = self.generateTargetsTreeData(pkgs, 'build')
        bb.event.fire(bb.event.TargetsTreeGenerated(tree), self.configuration.data)

    def buildWorldTargetList(self):
        """
         Build package list for "bitbake world"
        """
        all_depends = self.status.all_depends
        pn_provides = self.status.pn_provides
        parselog.debug(1, "collating packages for \"world\"")
        for f in self.status.possible_world:
            terminal = True
            pn = self.status.pkg_fn[f]

            for p in pn_provides[pn]:
                if p.startswith('virtual/'):
                    parselog.debug(2, "World build skipping %s due to %s provider starting with virtual/", f, p)
                    terminal = False
                    break
                for pf in self.status.providers[p]:
                    if self.status.pkg_fn[pf] != pn:
                        parselog.debug(2, "World build skipping %s due to both us and %s providing %s", f, pf, p)
                        terminal = False
                        break
            if terminal:
                self.status.world_target.add(pn)

    def interactiveMode( self ):
        """Drop off into a shell"""
        try:
            from bb import shell
        except ImportError:
            parselog.exception("Interactive mode not available")
            sys.exit(1)
        else:
            shell.start( self )

    def _findLayerConf(self):
        path = os.getcwd()
        while path != "/":
            bblayers = os.path.join(path, "conf", "bblayers.conf")
            if os.path.exists(bblayers):
                return bblayers

            path, _ = os.path.split(path)

    def parseConfigurationFiles(self, files):
        data = self.configuration.data
        bb.parse.init_parser(data)
        for f in files:
            data = _parse(f, data)

        layerconf = self._findLayerConf()
        if layerconf:
            parselog.debug(2, "Found bblayers.conf (%s)", layerconf)
            data = _parse(layerconf, data)

            layers = (bb.data.getVar('BBLAYERS', data, True) or "").split()

            data = bb.data.createCopy(data)
            for layer in layers:
                parselog.debug(2, "Adding layer %s", layer)
                bb.data.setVar('LAYERDIR', layer, data)
                data = _parse(os.path.join(layer, "conf", "layer.conf"), data)
                data.expandVarref('LAYERDIR')

            bb.data.delVar('LAYERDIR', data)

        if not data.getVar("BBPATH", True):
            raise SystemExit("The BBPATH variable is not set")

        data = _parse(os.path.join("conf", "bitbake.conf"), data)

        # Handle any INHERITs and inherit the base class
        bbclasses  = ["base"] + (data.getVar('INHERIT', True) or "").split()
        for bbclass in bbclasses:
            data = _inherit(bbclass, data)

        # Nomally we only register event handlers at the end of parsing .bb files
        # We register any handlers we've found so far here...
        for var in bb.data.getVar('__BBHANDLERS', data) or []:
            bb.event.register(var, bb.data.getVar(var, data))

        bb.fetch.fetcher_init(data)
        bb.codeparser.parser_cache_init(data)
        bb.parse.init_parser(data)
        bb.event.fire(bb.event.ConfigParsed(), data)
        self.configuration.data = data

    def handleCollections( self, collections ):
        """Handle collections"""
        if collections:
            collection_list = collections.split()
            for c in collection_list:
                regex = bb.data.getVar("BBFILE_PATTERN_%s" % c, self.configuration.data, 1)
                if regex == None:
                    parselog.error("BBFILE_PATTERN_%s not defined" % c)
                    continue
                priority = bb.data.getVar("BBFILE_PRIORITY_%s" % c, self.configuration.data, 1)
                if priority == None:
                    parselog.error("BBFILE_PRIORITY_%s not defined" % c)
                    continue
                try:
                    cre = re.compile(regex)
                except re.error:
                    parselog.error("BBFILE_PATTERN_%s \"%s\" is not a valid regular expression", c, regex)
                    continue
                try:
                    pri = int(priority)
                    self.status.bbfile_config_priorities.append((c, regex, cre, pri))
                except ValueError:
                    parselog.error("invalid value for BBFILE_PRIORITY_%s: \"%s\"", c, priority)

    def buildSetVars(self):
        """
        Setup any variables needed before starting a build
        """
        if not bb.data.getVar("BUILDNAME", self.configuration.data):
            bb.data.setVar("BUILDNAME", time.strftime('%Y%m%d%H%M'), self.configuration.data)
        bb.data.setVar("BUILDSTART", time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime()), self.configuration.data)

    def matchFiles(self, buildfile):
        """
        Find the .bb files which match the expression in 'buildfile'.
        """

        bf = os.path.abspath(buildfile)
        filelist, masked = self.collect_bbfiles()
        try:
            os.stat(bf)
            return [bf]
        except OSError:
            regexp = re.compile(buildfile)
            matches = []
            for f in filelist:
                if regexp.search(f) and os.path.isfile(f):
                    bf = f
                    matches.append(f)
            return matches

    def matchFile(self, buildfile):
        """
        Find the .bb file which matches the expression in 'buildfile'.
        Raise an error if multiple files
        """
        matches = self.matchFiles(buildfile)
        if len(matches) != 1:
            parselog.error("Unable to match %s (%s matches found):" % (buildfile, len(matches)))
            for f in matches:
                parselog.error("    %s" % f)
            raise MultipleMatches
        return matches[0]

    def buildFile(self, buildfile, task):
        """
        Build the file matching regexp buildfile
        """

        # Parse the configuration here. We need to do it explicitly here since
        # buildFile() doesn't use the cache
        self.parseConfiguration()

        # If we are told to do the None task then query the default task
        if (task == None):
            task = self.configuration.cmd

        fn, cls = bb.cache.Cache.virtualfn2realfn(buildfile)
        fn = os.path.abspath(fn)
        buildfile = self.matchFile(fn)

        self.buildSetVars()

        self.status = bb.cache.CacheData()
        infos = bb.cache.Cache.parse(fn, self.get_file_appends(fn), \
                                     self.configuration.data)
        infos = dict(infos)

        fn = bb.cache.Cache.realfn2virtual(buildfile, cls)
        try:
            maininfo = infos[fn]
        except KeyError:
            bb.fatal("%s does not exist" % fn)
        self.status.add_from_recipeinfo(fn, maininfo)

        # Tweak some variables
        item = maininfo.pn
        self.status.ignored_dependencies = set()
        self.status.bbfile_priority[fn] = 1

        # Remove external dependencies
        self.status.task_deps[fn]['depends'] = {}
        self.status.deps[fn] = []
        self.status.rundeps[fn] = []
        self.status.runrecs[fn] = []

        # Remove stamp for target if force mode active
        if self.configuration.force:
            logger.verbose("Remove stamp %s, %s", task, fn)
            bb.build.del_stamp('do_%s' % task, self.status, fn)

        # Setup taskdata structure
        taskdata = bb.taskdata.TaskData(self.configuration.abort)
        taskdata.add_provider(self.configuration.data, self.status, item)

        buildname = bb.data.getVar("BUILDNAME", self.configuration.data)
        bb.event.fire(bb.event.BuildStarted(buildname, [item]), self.configuration.event_data)

        # Execute the runqueue
        runlist = [[item, "do_%s" % task]]

        rq = bb.runqueue.RunQueue(self, self.configuration.data, self.status, taskdata, runlist)

        def buildFileIdle(server, rq, abort):

            if abort or self.state == state.stop:
                rq.finish_runqueue(True)
            elif self.state == state.shutdown:
                rq.finish_runqueue(False)
            failures = 0
            try:
                retval = rq.execute_runqueue()
            except runqueue.TaskFailure as exc:
                for fnid in exc.args:
                    buildlog.error("'%s' failed" % taskdata.fn_index[fnid])
                failures += len(exc.args)
                retval = False
            except SystemExit as exc:
                self.command.finishAsyncCommand()
                return False

            if not retval:
                bb.event.fire(bb.event.BuildCompleted(buildname, item, failures), self.configuration.event_data)
                self.command.finishAsyncCommand()
                return False
            if retval is True:
                return True
            return 0.5

        self.server_registration_cb(buildFileIdle, rq)

    def buildTargets(self, targets, task):
        """
        Attempt to build the targets specified
        """

        # Need files parsed
        self.updateCache()

        # If we are told to do the NULL task then query the default task
        if (task == None):
            task = self.configuration.cmd

        targets = self.checkPackages(targets)

        def buildTargetsIdle(server, rq, abort):
            if abort or self.state == state.stop:
                rq.finish_runqueue(True)
            elif self.state == state.shutdown:
                rq.finish_runqueue(False)
            failures = 0
            try:
                retval = rq.execute_runqueue()
            except runqueue.TaskFailure as exc:
                for fnid in exc.args:
                    buildlog.error("'%s' failed" % taskdata.fn_index[fnid])
                failures += len(exc.args)
                retval = False
            except SystemExit as exc:
                self.command.finishAsyncCommand()
                return False

            if not retval:
                bb.event.fire(bb.event.BuildCompleted(buildname, targets, failures), self.configuration.event_data)
                self.command.finishAsyncCommand()
                return False
            if retval is True:
                return True
            return 0.5

        self.buildSetVars()

        buildname = bb.data.getVar("BUILDNAME", self.configuration.data)
        bb.event.fire(bb.event.BuildStarted(buildname, targets), self.configuration.event_data)

        localdata = data.createCopy(self.configuration.data)
        bb.data.update_data(localdata)
        bb.data.expandKeys(localdata)

        taskdata = bb.taskdata.TaskData(self.configuration.abort)

        runlist = []
        for k in targets:
            taskdata.add_provider(localdata, self.status, k)
            runlist.append([k, "do_%s" % task])
        taskdata.add_unresolved(localdata, self.status)

        rq = bb.runqueue.RunQueue(self, self.configuration.data, self.status, taskdata, runlist)

        self.server_registration_cb(buildTargetsIdle, rq)

    def updateCache(self):
        if self.state == state.running:
            return

        if self.state in (state.shutdown, state.stop):
            self.parser.shutdown(clean=False)
            sys.exit(1)

        if self.state != state.parsing:
            self.parseConfiguration ()

            # Import Psyco if available and not disabled
            import platform
            if platform.machine() in ['i386', 'i486', 'i586', 'i686']:
                if not self.configuration.disable_psyco:
                    try:
                        import psyco
                    except ImportError:
                        collectlog.info("Psyco JIT Compiler (http://psyco.sf.net) not available. Install it to increase performance.")
                    else:
                        psyco.bind( CookerParser.parse_next )
                else:
                    collectlog.info("You have disabled Psyco. This decreases performance.")

            self.status = bb.cache.CacheData()

            ignore = bb.data.getVar("ASSUME_PROVIDED", self.configuration.data, 1) or ""
            self.status.ignored_dependencies = set(ignore.split())

            for dep in self.configuration.extra_assume_provided:
                self.status.ignored_dependencies.add(dep)

            self.handleCollections( bb.data.getVar("BBFILE_COLLECTIONS", self.configuration.data, 1) )

            (filelist, masked) = self.collect_bbfiles()
            bb.data.renameVar("__depends", "__base_depends", self.configuration.data)

            self.parser = CookerParser(self, filelist, masked)
            self.state = state.parsing

        if not self.parser.parse_next():
            collectlog.debug(1, "parsing complete")
            self.buildDepgraph()
            self.state = state.running
            return None

        return True

    def checkPackages(self, pkgs_to_build):

        if len(pkgs_to_build) == 0:
            raise NothingToBuild

        if 'world' in pkgs_to_build:
            self.buildWorldTargetList()
            pkgs_to_build.remove('world')
            for t in self.status.world_target:
                pkgs_to_build.append(t)

        return pkgs_to_build

    def get_bbfiles( self, path = os.getcwd() ):
        """Get list of default .bb files by reading out the current directory"""
        contents = os.listdir(path)
        bbfiles = []
        for f in contents:
            (root, ext) = os.path.splitext(f)
            if ext == ".bb":
                bbfiles.append(os.path.abspath(os.path.join(os.getcwd(), f)))
        return bbfiles

    def find_bbfiles( self, path ):
        """Find all the .bb and .bbappend files in a directory"""
        from os.path import join

        found = []
        for dir, dirs, files in os.walk(path):
            for ignored in ('SCCS', 'CVS', '.svn'):
                if ignored in dirs:
                    dirs.remove(ignored)
            found += [join(dir, f) for f in files if (f.endswith('.bb') or f.endswith('.bbappend'))]

        return found

    def collect_bbfiles( self ):
        """Collect all available .bb build files"""
        parsed, cached, skipped, masked = 0, 0, 0, 0

        collectlog.debug(1, "collecting .bb files")

        files = (data.getVar( "BBFILES", self.configuration.data, 1 ) or "").split()
        data.setVar("BBFILES", " ".join(files), self.configuration.data)

        if not len(files):
            files = self.get_bbfiles()

        if not len(files):
            collectlog.error("no recipe files to build, check your BBPATH and BBFILES?")
            bb.event.fire(CookerExit(), self.configuration.event_data)

        newfiles = set()
        for f in files:
            if os.path.isdir(f):
                dirfiles = self.find_bbfiles(f)
                newfiles.update(dirfiles)
            else:
                globbed = glob.glob(f)
                if not globbed and os.path.exists(f):
                    globbed = [f]
                newfiles.update(globbed)

        bbmask = bb.data.getVar('BBMASK', self.configuration.data, 1)

        if bbmask:
            try:
                bbmask_compiled = re.compile(bbmask)
            except sre_constants.error:
                collectlog.critical("BBMASK is not a valid regular expression, ignoring.")
                return list(newfiles), 0

        bbfiles = []
        bbappend = []
        for f in newfiles:
            if bbmask and bbmask_compiled.search(f):
                collectlog.debug(1, "skipping masked file %s", f)
                masked += 1
                continue
            if f.endswith('.bb'):
                bbfiles.append(f)
            elif f.endswith('.bbappend'):
                bbappend.append(f)
            else:
                collectlog.debug(1, "skipping %s: unknown file extension", f)

        # Build a list of .bbappend files for each .bb file
        for f in bbappend:
            base = os.path.basename(f).replace('.bbappend', '.bb')
            if not base in self.appendlist:
               self.appendlist[base] = []
            self.appendlist[base].append(f)

        return (bbfiles, masked)

    def get_file_appends(self, fn):
        """
        Returns a list of .bbappend files to apply to fn
        NB: collect_bbfiles() must have been called prior to this
        """
        f = os.path.basename(fn)
        if f in self.appendlist:
            return self.appendlist[f]
        return []

    def shutdown(self):
        self.state = state.shutdown

    def stop(self):
        self.state = state.stop

class CookerExit(bb.event.Event):
    """
    Notify clients of the Cooker shutdown
    """

    def __init__(self):
        bb.event.Event.__init__(self)

def catch_parse_error(func):
    """Exception handling bits for our parsing"""
    @wraps(func)
    def wrapped(fn, *args):
        try:
            return func(fn, *args)
        except (IOError, bb.parse.ParseError) as exc:
            parselog.critical("Unable to parse %s: %s" % (fn, exc))
            sys.exit(1)
    return wrapped

@catch_parse_error
def _parse(fn, data, include=False):
    return bb.parse.handle(fn, data, include)

@catch_parse_error
def _inherit(bbclass, data):
    bb.parse.BBHandler.inherit([bbclass], data)
    return data

class ParsingFailure(Exception):
    def __init__(self, realexception, recipe):
        self.realexception = realexception
        self.recipe = recipe
        Exception.__init__(self, "Failure when parsing %s" % recipe)
        self.args = (realexception, recipe)

def parse_file(task):
    filename, appends = task
    try:
        return True, bb.cache.Cache.parse(filename, appends, parse_file.cfg)
    except Exception, exc:
        exc.recipe = filename
        raise exc
    # Need to turn BaseExceptions into Exceptions here so we gracefully shutdown
    # and for example a worker thread doesn't just exit on its own in response to
    # a SystemExit event for example.
    except BaseException, exc:
        raise ParsingFailure(exc, filename)

class CookerParser(object):
    def __init__(self, cooker, filelist, masked):
        self.filelist = filelist
        self.cooker = cooker
        self.cfgdata = cooker.configuration.data

        # Accounting statistics
        self.parsed = 0
        self.cached = 0
        self.error = 0
        self.masked = masked

        self.skipped = 0
        self.virtuals = 0
        self.total = len(filelist)

        self.current = 0
        self.num_processes = int(self.cfgdata.getVar("BB_NUMBER_PARSE_THREADS", True) or
                                 multiprocessing.cpu_count())

        self.bb_cache = bb.cache.Cache(self.cfgdata)
        self.fromcache = []
        self.willparse = []
        for filename in self.filelist:
            appends = self.cooker.get_file_appends(filename)
            if not self.bb_cache.cacheValid(filename):
                self.willparse.append((filename, appends))
            else:
                self.fromcache.append((filename, appends))
        self.toparse = self.total - len(self.fromcache)
        self.progress_chunk = max(self.toparse / 100, 1)

        self.start()

    def start(self):
        def init(cfg):
            parse_file.cfg = cfg

        self.results = self.load_cached()

        if self.toparse:
            bb.event.fire(bb.event.ParseStarted(self.toparse), self.cfgdata)

            self.pool = multiprocessing.Pool(self.num_processes, init, [self.cfgdata])
            parsed = self.pool.imap(parse_file, self.willparse)
            self.pool.close()

            self.results = itertools.chain(self.results, parsed)

    def shutdown(self, clean=True):
        if not self.toparse:
            return

        if clean:
            event = bb.event.ParseCompleted(self.cached, self.parsed,
                                            self.skipped, self.masked,
                                            self.virtuals, self.error,
                                            self.total)
            bb.event.fire(event, self.cfgdata)
        else:
            self.pool.terminate()
        self.pool.join()

        bb.codeparser.parser_cache_save(self.cfgdata)

        sync = threading.Thread(target=self.bb_cache.sync)
        sync.start()
        multiprocessing.util.Finalize(None, sync.join, exitpriority=-100)

    def load_cached(self):
        for filename, appends in self.fromcache:
            cached, infos = self.bb_cache.load(filename, appends, self.cfgdata)
            yield not cached, infos

    def parse_next(self):
        try:
            parsed, result = self.results.next()
        except StopIteration:
            self.shutdown()
            return False
        except Exception as exc:
            self.shutdown(clean=False)
            bb.fatal('Error parsing %s: %s' % (exc.recipe, exc))

        self.current += 1
        self.virtuals += len(result)
        if parsed:
            self.parsed += 1
            if self.parsed % self.progress_chunk == 0:
                bb.event.fire(bb.event.ParseProgress(self.parsed),
                              self.cfgdata)
        else:
            self.cached += 1

        for virtualfn, info in result:
            if info.skipped:
                self.skipped += 1
            else:
                self.bb_cache.add_info(virtualfn, info, self.cooker.status,
                                        parsed=parsed)
        return True

    def reparse(self, filename):
        infos = self.bb_cache.parse(filename,
                                    self.cooker.get_file_appends(filename),
                                    self.cfgdata)
        for vfn, info in infos:
            self.cooker.status.add_from_recipeinfo(vfn, info)
