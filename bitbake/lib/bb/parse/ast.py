# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
"""
 AbstractSyntaxTree classes for the Bitbake language
"""

# Copyright (C) 2003, 2004 Chris Larson
# Copyright (C) 2003, 2004 Phil Blundell
# Copyright (C) 2009 Holger Hans Peter Freyther
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import
from future_builtins import filter
import re
import string
import logging
import bb
import itertools
from bb import methodpool
from bb.parse import logger

__parsed_methods__ = bb.methodpool.get_parsed_dict()
_bbversions_re = re.compile(r"\[(?P<from>[0-9]+)-(?P<to>[0-9]+)\]")

class StatementGroup(list):
    def eval(self, data):
        for statement in self:
            statement.eval(data)

class AstNode(object):
    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

class IncludeNode(AstNode):
    def __init__(self, filename, lineno, what_file, force):
        AstNode.__init__(self, filename, lineno)
        self.what_file = what_file
        self.force = force

    def eval(self, data):
        """
        Include the file and evaluate the statements
        """
        s = bb.data.expand(self.what_file, data)
        logger.debug(2, "CONF %s:%s: including %s", self.filename, self.lineno, s)

        # TODO: Cache those includes... maybe not here though
        if self.force:
            bb.parse.ConfHandler.include(self.filename, s, data, "include required")
        else:
            bb.parse.ConfHandler.include(self.filename, s, data, False)

class ExportNode(AstNode):
    def __init__(self, filename, lineno, var):
        AstNode.__init__(self, filename, lineno)
        self.var = var

    def eval(self, data):
        bb.data.setVarFlag(self.var, "export", 1, data)

class DataNode(AstNode):
    """
    Various data related updates. For the sake of sanity
    we have one class doing all this. This means that all
    this need to be re-evaluated... we might be able to do
    that faster with multiple classes.
    """
    def __init__(self, filename, lineno, groupd):
        AstNode.__init__(self, filename, lineno)
        self.groupd = groupd

    def getFunc(self, key, data):
        if 'flag' in self.groupd and self.groupd['flag'] != None:
            return data.getVarFlag(key, self.groupd['flag'], noweakdefault=True)
        else:
            return data.getVar(key, noweakdefault=True)

    def eval(self, data):
        groupd = self.groupd
        key = groupd["var"]
        if "exp" in groupd and groupd["exp"] != None:
            bb.data.setVarFlag(key, "export", 1, data)
        if "ques" in groupd and groupd["ques"] != None:
            val = self.getFunc(key, data)
            if val == None:
                val = groupd["value"]
        elif "colon" in groupd and groupd["colon"] != None:
            e = data.createCopy()
            bb.data.update_data(e)
            val = bb.data.expand(groupd["value"], e, key + "[:=]")
        elif "append" in groupd and groupd["append"] != None:
            val = "%s %s" % ((self.getFunc(key, data) or ""), groupd["value"])
        elif "prepend" in groupd and groupd["prepend"] != None:
            val = "%s %s" % (groupd["value"], (self.getFunc(key, data) or ""))
        elif "postdot" in groupd and groupd["postdot"] != None:
            val = "%s%s" % ((self.getFunc(key, data) or ""), groupd["value"])
        elif "predot" in groupd and groupd["predot"] != None:
            val = "%s%s" % (groupd["value"], (self.getFunc(key, data) or ""))
        else:
            val = groupd["value"]

        if 'flag' in groupd and groupd['flag'] != None:
            bb.data.setVarFlag(key, groupd['flag'], val, data)
        elif groupd["lazyques"]:
            bb.data.setVarFlag(key, "defaultval", val, data)
        else:
            bb.data.setVar(key, val, data)

class MethodNode(AstNode):
    def __init__(self, filename, lineno, func_name, body):
        AstNode.__init__(self, filename, lineno)
        self.func_name = func_name
        self.body = body

    def eval(self, data):
        if self.func_name == "__anonymous":
            funcname = ("__anon_%s_%s" % (self.lineno, self.filename.translate(string.maketrans('/.+-', '____'))))
            if not funcname in bb.methodpool._parsed_fns:
                text = "def %s(d):\n" % (funcname) + '\n'.join(self.body)
                bb.methodpool.insert_method(funcname, text, self.filename)
            anonfuncs = bb.data.getVar('__BBANONFUNCS', data) or []
            anonfuncs.append(funcname)
            bb.data.setVar('__BBANONFUNCS', anonfuncs, data)
        else:
            bb.data.setVarFlag(self.func_name, "func", 1, data)
            bb.data.setVar(self.func_name, '\n'.join(self.body), data)

class PythonMethodNode(AstNode):
    def __init__(self, filename, lineno, function, define, body):
        AstNode.__init__(self, filename, lineno)
        self.function = function
        self.define = define
        self.body = body

    def eval(self, data):
        # Note we will add root to parsedmethods after having parse
        # 'this' file. This means we will not parse methods from
        # bb classes twice
        text = '\n'.join(self.body)
        if not bb.methodpool.parsed_module(self.define):
            bb.methodpool.insert_method(self.define, text, self.filename)
        bb.data.setVarFlag(self.function, "func", 1, data)
        bb.data.setVarFlag(self.function, "python", 1, data)
        bb.data.setVar(self.function, text, data)

class MethodFlagsNode(AstNode):
    def __init__(self, filename, lineno, key, m):
        AstNode.__init__(self, filename, lineno)
        self.key = key
        self.m = m

    def eval(self, data):
        if bb.data.getVar(self.key, data):
            # clean up old version of this piece of metadata, as its
            # flags could cause problems
            bb.data.setVarFlag(self.key, 'python', None, data)
            bb.data.setVarFlag(self.key, 'fakeroot', None, data)
        if self.m.group("py") is not None:
            bb.data.setVarFlag(self.key, "python", "1", data)
        else:
            bb.data.delVarFlag(self.key, "python", data)
        if self.m.group("fr") is not None:
            bb.data.setVarFlag(self.key, "fakeroot", "1", data)
        else:
            bb.data.delVarFlag(self.key, "fakeroot", data)

class ExportFuncsNode(AstNode):
    def __init__(self, filename, lineno, fns, classes):
        AstNode.__init__(self, filename, lineno)
        self.n = fns.split()
        self.classes = classes

    def eval(self, data):
        for f in self.n:
            allvars = []
            allvars.append(f)
            allvars.append(self.classes[-1] + "_" + f)

            vars = [[ allvars[0], allvars[1] ]]
            if len(self.classes) > 1 and self.classes[-2] is not None:
                allvars.append(self.classes[-2] + "_" + f)
                vars = []
                vars.append([allvars[2], allvars[1]])
                vars.append([allvars[0], allvars[2]])

            for (var, calledvar) in vars:
                if bb.data.getVar(var, data) and not bb.data.getVarFlag(var, 'export_func', data):
                    continue

                if bb.data.getVar(var, data):
                    bb.data.setVarFlag(var, 'python', None, data)
                    bb.data.setVarFlag(var, 'func', None, data)

                for flag in [ "func", "python" ]:
                    if bb.data.getVarFlag(calledvar, flag, data):
                        bb.data.setVarFlag(var, flag, bb.data.getVarFlag(calledvar, flag, data), data)
                for flag in [ "dirs" ]:
                    if bb.data.getVarFlag(var, flag, data):
                        bb.data.setVarFlag(calledvar, flag, bb.data.getVarFlag(var, flag, data), data)

                if bb.data.getVarFlag(calledvar, "python", data):
                    bb.data.setVar(var, "\tbb.build.exec_func('" + calledvar + "', d)\n", data)
                else:
                    bb.data.setVar(var, "\t" + calledvar + "\n", data)
                bb.data.setVarFlag(var, 'export_func', '1', data)

class AddTaskNode(AstNode):
    def __init__(self, filename, lineno, func, before, after):
        AstNode.__init__(self, filename, lineno)
        self.func = func
        self.before = before
        self.after = after

    def eval(self, data):
        var = self.func
        if self.func[:3] != "do_":
            var = "do_" + self.func

        bb.data.setVarFlag(var, "task", 1, data)
        bbtasks = bb.data.getVar('__BBTASKS', data) or []
        if not var in bbtasks:
            bbtasks.append(var)
        bb.data.setVar('__BBTASKS', bbtasks, data)

        existing = bb.data.getVarFlag(var, "deps", data) or []
        if self.after is not None:
            # set up deps for function
            for entry in self.after.split():
                if entry not in existing:
                    existing.append(entry)
        bb.data.setVarFlag(var, "deps", existing, data)
        if self.before is not None:
            # set up things that depend on this func
            for entry in self.before.split():
                existing = bb.data.getVarFlag(entry, "deps", data) or []
                if var not in existing:
                    bb.data.setVarFlag(entry, "deps", [var] + existing, data)

class BBHandlerNode(AstNode):
    def __init__(self, filename, lineno, fns):
        AstNode.__init__(self, filename, lineno)
        self.hs = fns.split()

    def eval(self, data):
        bbhands = bb.data.getVar('__BBHANDLERS', data) or []
        for h in self.hs:
            bbhands.append(h)
            bb.data.setVarFlag(h, "handler", 1, data)
        bb.data.setVar('__BBHANDLERS', bbhands, data)

class InheritNode(AstNode):
    def __init__(self, filename, lineno, classes):
        AstNode.__init__(self, filename, lineno)
        self.classes = classes

    def eval(self, data):
        bb.parse.BBHandler.inherit(self.classes, data)

def handleInclude(statements, filename, lineno, m, force):
    statements.append(IncludeNode(filename, lineno, m.group(1), force))

def handleExport(statements, filename, lineno, m):
    statements.append(ExportNode(filename, lineno, m.group(1)))

def handleData(statements, filename, lineno, groupd):
    statements.append(DataNode(filename, lineno, groupd))

def handleMethod(statements, filename, lineno, func_name, body):
    statements.append(MethodNode(filename, lineno, func_name, body))

def handlePythonMethod(statements, filename, lineno, funcname, root, body):
    statements.append(PythonMethodNode(filename, lineno, funcname, root, body))

def handleMethodFlags(statements, filename, lineno, key, m):
    statements.append(MethodFlagsNode(filename, lineno, key, m))

def handleExportFuncs(statements, filename, lineno, m, classes):
    statements.append(ExportFuncsNode(filename, lineno, m.group(1), classes))

def handleAddTask(statements, filename, lineno, m):
    func = m.group("func")
    before = m.group("before")
    after = m.group("after")
    if func is None:
        return

    statements.append(AddTaskNode(filename, lineno, func, before, after))

def handleBBHandlers(statements, filename, lineno, m):
    statements.append(BBHandlerNode(filename, lineno, m.group(1)))

def handleInherit(statements, filename, lineno, m):
    classes = m.group(1)
    statements.append(InheritNode(filename, lineno, classes.split()))

def finalize(fn, d, variant = None):
    all_handlers = {}
    for var in bb.data.getVar('__BBHANDLERS', d) or []:
        # try to add the handler
        handler = bb.data.getVar(var, d)
        bb.event.register(var, handler)

    bb.event.fire(bb.event.RecipePreFinalise(fn), d)

    bb.data.expandKeys(d)
    bb.data.update_data(d)
    code = []
    for funcname in bb.data.getVar("__BBANONFUNCS", d) or []:
        code.append("%s(d)" % funcname)
    bb.utils.simple_exec("\n".join(code), {"d": d})
    bb.data.update_data(d)

    tasklist = bb.data.getVar('__BBTASKS', d) or []
    bb.build.add_tasks(tasklist, d)

    bb.parse.siggen.finalise(fn, d, variant)

    bb.event.fire(bb.event.RecipeParsed(fn), d)

def _create_variants(datastores, names, function):
    def create_variant(name, orig_d, arg = None):
        new_d = bb.data.createCopy(orig_d)
        function(arg or name, new_d)
        datastores[name] = new_d

    for variant, variant_d in datastores.items():
        for name in names:
            if not variant:
                # Based on main recipe
                create_variant(name, variant_d)
            else:
                create_variant("%s-%s" % (variant, name), variant_d, name)

def _expand_versions(versions):
    def expand_one(version, start, end):
        for i in xrange(start, end + 1):
            ver = _bbversions_re.sub(str(i), version, 1)
            yield ver

    versions = iter(versions)
    while True:
        try:
            version = next(versions)
        except StopIteration:
            break

        range_ver = _bbversions_re.search(version)
        if not range_ver:
            yield version
        else:
            newversions = expand_one(version, int(range_ver.group("from")),
                                     int(range_ver.group("to")))
            versions = itertools.chain(newversions, versions)

def multi_finalize(fn, d):
    appends = (d.getVar("__BBAPPEND", True) or "").split()
    for append in appends:
        logger.debug(2, "Appending .bbappend file %s to %s", append, fn)
        bb.parse.BBHandler.handle(append, d, True)

    onlyfinalise = d.getVar("__ONLYFINALISE", False)

    safe_d = d
    d = bb.data.createCopy(safe_d)
    try:
        finalize(fn, d)
    except bb.parse.SkipPackage as e:
        bb.data.setVar("__SKIPPED", e.args[0], d)
    datastores = {"": safe_d}

    versions = (d.getVar("BBVERSIONS", True) or "").split()
    if versions:
        pv = orig_pv = d.getVar("PV", True)
        baseversions = {}

        def verfunc(ver, d, pv_d = None):
            if pv_d is None:
                pv_d = d

            overrides = d.getVar("OVERRIDES", True).split(":")
            pv_d.setVar("PV", ver)
            overrides.append(ver)
            bpv = baseversions.get(ver) or orig_pv
            pv_d.setVar("BPV", bpv)
            overrides.append(bpv)
            d.setVar("OVERRIDES", ":".join(overrides))

        versions = list(_expand_versions(versions))
        for pos, version in enumerate(list(versions)):
            try:
                pv, bpv = version.split(":", 2)
            except ValueError:
                pass
            else:
                versions[pos] = pv
                baseversions[pv] = bpv

        if pv in versions and not baseversions.get(pv):
            versions.remove(pv)
        else:
            pv = versions.pop()

            # This is necessary because our existing main datastore
            # has already been finalized with the old PV, we need one
            # that's been finalized with the new PV.
            d = bb.data.createCopy(safe_d)
            verfunc(pv, d, safe_d)
            try:
                finalize(fn, d)
            except bb.parse.SkipPackage as e:
                bb.data.setVar("__SKIPPED", e.args[0], d)

        _create_variants(datastores, versions, verfunc)

    extended = d.getVar("BBCLASSEXTEND", True) or ""
    if extended:
        # the following is to support bbextends with argument, for e.g. multilib
        # an example is as follow:
        #   BBCLASSEXTEND = "multilib:lib32"
        # it will create foo-lib32, inheriting multilib.bbclass and set
        # CURRENTEXTEND to "lib32"
        extendedmap = {}

        for ext in extended.split():
            eext = ext.split(':')
            if len(eext) > 1:
                extendedmap[eext[1]] = eext[0]
            else:
                extendedmap[ext] = ext

        pn = d.getVar("PN", True)
        def extendfunc(name, d):
            if name != extendedmap[name]:
                d.setVar("BBEXTENDCURR", extendedmap[name])
                d.setVar("BBEXTENDVARIANT", name)
            else:
                d.setVar("PN", "%s-%s" % (pn, name))
            bb.parse.BBHandler.inherit([extendedmap[name]], d)

        safe_d.setVar("BBCLASSEXTEND", extended)
        _create_variants(datastores, extendedmap.keys(), extendfunc)

    for variant, variant_d in datastores.iteritems():
        if variant:
            try:
                if not onlyfinalise or variant in onlyfinalise:
                    finalize(fn, variant_d, variant)
            except bb.parse.SkipPackage as e:
                bb.data.setVar("__SKIPPED", e.args[0], variant_d)

    if len(datastores) > 1:
        variants = filter(None, datastores.iterkeys())
        safe_d.setVar("__VARIANTS", " ".join(variants))

    datastores[""] = d
    return datastores
