BB_DEFAULT_TASK ?= "build"

inherit patch
inherit staging

inherit mirrors
inherit utils
inherit utility-tasks
inherit metadata_scm
inherit buildstats

python sys_path_eh () {
    if isinstance(e, bb.event.ConfigParsed):
        import sys
        import os
        import time

        bbpath = e.data.getVar("BBPATH", True).split(":")
        sys.path[0:0] = [os.path.join(dir, "lib") for dir in bbpath]

        def inject(name, value):
            """Make a python object accessible from everywhere for the metadata"""
            if hasattr(bb.utils, "_context"):
                bb.utils._context[name] = value
            else:
                __builtins__[name] = value

        import oe.path
        import oe.utils
        inject("bb", bb)
        inject("sys", sys)
        inject("time", time)
        inject("oe", oe)
}

addhandler sys_path_eh

die() {
	oefatal "$*"
}

oenote() {
	echo "NOTE:" "$*"
}

oewarn() {
	echo "WARNING:" "$*"
}

oefatal() {
	echo "FATAL:" "$*"
	exit 1
}

oedebug() {
	test $# -ge 2 || {
		echo "Usage: oedebug level \"message\""
		exit 1
	}

	test ${OEDEBUG:-0} -ge $1 && {
		shift
		echo "DEBUG:" $*
	}
}

oe_runmake() {
	if [ x"$MAKE" = x ]; then MAKE=make; fi
	oenote ${MAKE} ${EXTRA_OEMAKE} "$@"
	${MAKE} ${EXTRA_OEMAKE} "$@" || die "oe_runmake failed"
}


def base_dep_prepend(d):
	#
	# Ideally this will check a flag so we will operate properly in
	# the case where host == build == target, for now we don't work in
	# that case though.
	#

	deps = ""
	# INHIBIT_DEFAULT_DEPS doesn't apply to the patch command.  Whether or  not
	# we need that built is the responsibility of the patch function / class, not
	# the application.
	if not bb.data.getVar('INHIBIT_DEFAULT_DEPS', d):
		if (bb.data.getVar('HOST_SYS', d, 1) !=
	     	    bb.data.getVar('BUILD_SYS', d, 1)):
			deps += " virtual/${TARGET_PREFIX}gcc virtual/${TARGET_PREFIX}compilerlibs virtual/libc "
	return deps

DEPENDS_prepend="${@base_dep_prepend(d)} "
DEPENDS_virtclass-native_prepend="${@base_dep_prepend(d)} "
DEPENDS_virtclass-nativesdk_prepend="${@base_dep_prepend(d)} "

FILESPATH = "${@base_set_filespath([ "${FILE_DIRNAME}/${PF}", "${FILE_DIRNAME}/${P}", "${FILE_DIRNAME}/${PN}", "${FILE_DIRNAME}/${BP}", "${FILE_DIRNAME}/${BPN}", "${FILE_DIRNAME}/files", "${FILE_DIRNAME}" ], d)}"
# THISDIR only works properly with imediate expansion as it has to run
# in the context of the location its used (:=)
THISDIR = "${@os.path.dirname(bb.data.getVar('FILE', d, True))}"

addtask fetch
do_fetch[dirs] = "${DL_DIR}"
python base_do_fetch() {

	src_uri = (bb.data.getVar('SRC_URI', d, True) or "").split()
	if len(src_uri) == 0:
		return

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

        try:
            fetcher = bb.fetch2.Fetch(src_uri, localdata)
            fetcher.download()
        except bb.fetch2.BBFetchException, e:
            raise bb.build.FuncFailed(e)
}

addtask unpack after do_fetch
do_unpack[dirs] = "${WORKDIR}"
python base_do_unpack() {
	src_uri = (bb.data.getVar('SRC_URI', d, True) or "").split()
	if len(src_uri) == 0:
		return

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

	rootdir = bb.data.getVar('WORKDIR', localdata, True)

        try:
            fetcher = bb.fetch2.Fetch(src_uri, localdata)
            fetcher.unpack(rootdir)
        except bb.fetch2.BBFetchException, e:
            raise bb.build.FuncFailed(e)
}

GIT_CONFIG = "${STAGING_DIR_NATIVE}/usr/etc/gitconfig"

def generate_git_config(e):
        from bb import data

        if data.getVar('GIT_CORE_CONFIG', e.data, True):
                gitconfig_path = bb.data.getVar('GIT_CONFIG', e.data, True)
                proxy_command = "    gitproxy = %s\n" % data.getVar('GIT_PROXY_COMMAND', e.data, True)

                bb.mkdirhier(bb.data.expand("${STAGING_DIR_NATIVE}/usr/etc/", e.data))
                if (os.path.exists(gitconfig_path)):
                        os.remove(gitconfig_path)

                f = open(gitconfig_path, 'w')
                f.write("[core]\n")
                ignore_hosts = data.getVar('GIT_PROXY_IGNORE', e.data, True).split()
                for ignore_host in ignore_hosts:
                        f.write("    gitproxy = none for %s\n" % ignore_host)
                f.write(proxy_command)
                f.close

addhandler base_eventhandler
python base_eventhandler() {
	from bb import note, error, data
	from bb.event import getName

	messages = {}
	messages["Completed"] = "completed"
	messages["Succeeded"] = "completed"
	messages["Started"] = "started"
	messages["Failed"] = "failed"

	name = getName(e)
	msg = ""
	if name.startswith("Pkg"):
		msg += "package %s: " % data.getVar("P", e.data, 1)
		msg += messages.get(name[3:]) or name[3:]
	elif name.startswith("Task"):
		msg += "package %s: task %s: " % (data.getVar("PF", e.data, 1), e.task)
		msg += messages.get(name[4:]) or name[4:]
	elif name.startswith("Build"):
		msg += "build %s: " % e.name
		msg += messages.get(name[5:]) or name[5:]
	elif name == "UnsatisfiedDep":
		msg += "package %s: dependency %s %s" % (e.pkg, e.dep, name[:-3].lower())

	# Only need to output when using 1.8 or lower, the UI code handles it
	# otherwise
	if (int(bb.__version__.split(".")[0]) <= 1 and int(bb.__version__.split(".")[1]) <= 8):
		if msg:
			note(msg)

	if name.startswith("BuildStarted"):
		bb.data.setVar( 'BB_VERSION', bb.__version__, e.data )
		statusvars = ['BB_VERSION', 'METADATA_BRANCH', 'METADATA_REVISION', 'TARGET_ARCH', 'TARGET_OS', 'MACHINE', 'DISTRO', 'DISTRO_VERSION','TARGET_FPU']
		statuslines = ["%-17s = \"%s\"" % (i, bb.data.getVar(i, e.data, 1) or '') for i in statusvars]
		statusmsg = "\nOE Build Configuration:\n%s\n" % '\n'.join(statuslines)
		print statusmsg

		needed_vars = [ "TARGET_ARCH", "TARGET_OS" ]
		pesteruser = []
		for v in needed_vars:
			val = bb.data.getVar(v, e.data, 1)
			if not val or val == 'INVALID':
				pesteruser.append(v)
		if pesteruser:
			bb.fatal('The following variable(s) were not set: %s\nPlease set them directly, or choose a MACHINE or DISTRO that sets them.' % ', '.join(pesteruser))

        if name == "ConfigParsed":
                generate_git_config(e)

	if not data in e.__dict__:
		return

	log = data.getVar("EVENTLOG", e.data, 1)
	if log:
		logfile = file(log, "a")
		logfile.write("%s\n" % msg)
		logfile.close()
}

addtask configure after do_unpack do_patch
do_configure[dirs] = "${S} ${B}"
do_configure[deptask] = "do_populate_sysroot"
base_do_configure() {
	:
}

addtask compile after do_configure
do_compile[dirs] = "${S} ${B}"
base_do_compile() {
	if [ -e Makefile -o -e makefile ]; then
		oe_runmake || die "make failed"
	else
		oenote "nothing to compile"
	fi
}

addtask install after do_compile
do_install[dirs] = "${D} ${S} ${B}"
# Remove and re-create ${D} so that is it guaranteed to be empty
do_install[cleandirs] = "${D}"

base_do_install() {
	:
}

base_do_package() {
	:
}

addtask build after do_populate_sysroot
do_build = ""
do_build[func] = "1"
do_build[noexec] = "1"
do_build[recrdeptask] += "do_deploy"
do_build () {
	:
}

python () {
    import exceptions, string

    # If PRINC is set, try and increase the PR value by the amount specified
    princ = bb.data.getVar('PRINC', d, True)
    if princ:
        pr = bb.data.getVar('PR', d, True)
        start = -1
        end = -1
        for i in range(len(pr)):
            if pr[i] in string.digits:
                if start == -1:
                    start = i
                else:
                    end = i
        if start == -1 or end == -1:
            bb.error("Unable to analyse format of PR variable: %s" % pr)
        prval = pr[start:end+1]
        prval = int(prval) + int(princ)
        pr = pr[0:start] + str(prval) + pr[end:len(pr)-1]
        bb.data.setVar('PR', pr, d)

    pn = bb.data.getVar('PN', d, 1)
    license = bb.data.getVar('LICENSE', d, True)
    if license == "INVALID":
        bb.fatal('This recipe does not have the LICENSE field set (%s)' % pn)

    commercial_license = bb.data.getVar('COMMERCIAL_LICENSE', d, 1)
    import re
    pnr = pn.replace('+', "\+")
    if commercial_license and re.search(pnr, commercial_license):
        bb.debug(1, "Skipping %s because it's commercially licensed" % pn)
        raise bb.parse.SkipPackage("because it requires commercial license to ship product")

    # If we're building a target package we need to use fakeroot (pseudo)
    # in order to capture permissions, owners, groups and special files
    if not bb.data.inherits_class('native', d) and not bb.data.inherits_class('cross', d):
        deps = (bb.data.getVarFlag('do_install', 'depends', d) or "").split()
        deps.append('virtual/fakeroot-native:do_populate_sysroot')
        bb.data.setVarFlag('do_install', 'depends', " ".join(deps),d)
        bb.data.setVarFlag('do_install', 'fakeroot', 1, d)
        deps = (bb.data.getVarFlag('do_package', 'depends', d) or "").split()
        deps.append('virtual/fakeroot-native:do_populate_sysroot')
        bb.data.setVarFlag('do_package', 'depends', " ".join(deps),d)
        bb.data.setVarFlag('do_package', 'fakeroot', 1, d)
        bb.data.setVarFlag('do_package_setscene', 'fakeroot', 1, d)
    source_mirror_fetch = bb.data.getVar('SOURCE_MIRROR_FETCH', d, 0)
    if not source_mirror_fetch:
        need_host = bb.data.getVar('COMPATIBLE_HOST', d, 1)
        if need_host:
            import re
            this_host = bb.data.getVar('HOST_SYS', d, 1)
            if not re.match(need_host, this_host):
                raise bb.parse.SkipPackage("incompatible with host %s" % this_host)

        need_machine = bb.data.getVar('COMPATIBLE_MACHINE', d, 1)
        if need_machine:
            import re
            this_machine = bb.data.getVar('MACHINE', d, 1)
            if this_machine and not re.match(need_machine, this_machine):
                this_soc_family = bb.data.getVar('SOC_FAMILY', d, 1)
                if (this_soc_family and not re.match(need_machine, this_soc_family)) or not this_soc_family:
                    raise bb.parse.SkipPackage("incompatible with machine %s" % this_machine)


        dont_want_license = bb.data.getVar('INCOMPATIBLE_LICENSE', d, 1)
        if dont_want_license and not pn.endswith("-native") and not pn.endswith("-cross") and not pn.endswith("-cross-initial") and not pn.endswith("-cross-intermediate"):
            hosttools_whitelist = (bb.data.getVar('HOSTTOOLS_WHITELIST_%s' % dont_want_license, d, 1) or "").split()
            lgplv2_whitelist = (bb.data.getVar('LGPLv2_WHITELIST_%s' % dont_want_license, d, 1) or "").split()
            dont_want_whitelist = (bb.data.getVar('WHITELIST_%s' % dont_want_license, d, 1) or "").split()
            if pn not in hosttools_whitelist and pn not in lgplv2_whitelist and pn not in dont_want_whitelist:

                import re
                this_license = bb.data.getVar('LICENSE', d, 1)
                if this_license and re.search(dont_want_license, this_license):
                    bb.note("SKIPPING %s because it's %s" % (pn, this_license))
                    raise bb.parse.SkipPackage("incompatible with license %s" % this_license)

    # OBSOLETE in bitbake 1.7.4
    srcdate = bb.data.getVar('SRCDATE_%s' % pn, d, 1)
    if srcdate != None:
        bb.data.setVar('SRCDATE', srcdate, d)

    use_nls = bb.data.getVar('USE_NLS_%s' % pn, d, 1)
    if use_nls != None:
        bb.data.setVar('USE_NLS', use_nls, d)

    # Git packages should DEPEND on git-native
    srcuri = bb.data.getVar('SRC_URI', d, 1)
    if "git://" in srcuri:
        depends = bb.data.getVarFlag('do_fetch', 'depends', d) or ""
        depends = depends + " git-native:do_populate_sysroot"
        bb.data.setVarFlag('do_fetch', 'depends', depends, d)

    # Mercurial packages should DEPEND on mercurial-native
    elif "hg://" in srcuri:
        depends = bb.data.getVarFlag('do_fetch', 'depends', d) or ""
        depends = depends + " mercurial-native:do_populate_sysroot"
        bb.data.setVarFlag('do_fetch', 'depends', depends, d)

    # OSC packages should DEPEND on osc-native
    elif "osc://" in srcuri:
        depends = bb.data.getVarFlag('do_fetch', 'depends', d) or ""
        depends = depends + " osc-native:do_populate_sysroot"
        bb.data.setVarFlag('do_fetch', 'depends', depends, d)

    # bb.utils.sha256_file() will fail if hashlib isn't present, so we fallback
    # on shasum-native.  We need to ensure that it is staged before we fetch.
    if bb.data.getVar('PN', d, True) != "shasum-native":
        try:
            import hashlib
        except ImportError:
            depends = bb.data.getVarFlag('do_fetch', 'depends', d) or ""
            depends = depends + " shasum-native:do_populate_sysroot"
            bb.data.setVarFlag('do_fetch', 'depends', depends, d)

    # *.xz should depends on xz-native for unpacking
    # Not endswith because of "*.patch.xz;patch=1". Need bb.decodeurl in future
    if '.xz' in srcuri:
        depends = bb.data.getVarFlag('do_unpack', 'depends', d) or ""
        depends = depends + " xz-native:do_populate_sysroot"
        bb.data.setVarFlag('do_unpack', 'depends', depends, d)

    # 'multimachine' handling
    mach_arch = bb.data.getVar('MACHINE_ARCH', d, 1)
    pkg_arch = bb.data.getVar('PACKAGE_ARCH', d, 1)

    if (pkg_arch == mach_arch):
        # Already machine specific - nothing further to do
        return

    #
    # We always try to scan SRC_URI for urls with machine overrides
    # unless the package sets SRC_URI_OVERRIDES_PACKAGE_ARCH=0
    #
    override = bb.data.getVar('SRC_URI_OVERRIDES_PACKAGE_ARCH', d, 1)
    if override != '0':
        paths = []
        for p in [ "${PF}", "${P}", "${PN}", "files", "" ]:
            path = bb.data.expand(os.path.join("${FILE_DIRNAME}", p, "${MACHINE}"), d)
            if os.path.isdir(path):
                paths.append(path)
        if len(paths) != 0:
            for s in srcuri.split():
                if not s.startswith("file://"):
                    continue
                fetcher = bb.fetch2.Fetch([s], d)
                local = fetcher.localpath(s)
                for mp in paths:
                    if local.startswith(mp):
                        #bb.note("overriding PACKAGE_ARCH from %s to %s" % (pkg_arch, mach_arch))
                        bb.data.setVar('PACKAGE_ARCH', "${MACHINE_ARCH}", d)
                        bb.data.setVar('MULTIMACH_ARCH', mach_arch, d)
                        return

    multiarch = pkg_arch

    packages = bb.data.getVar('PACKAGES', d, 1).split()
    for pkg in packages:
        pkgarch = bb.data.getVar("PACKAGE_ARCH_%s" % pkg, d, 1)

        # We could look for != PACKAGE_ARCH here but how to choose
        # if multiple differences are present?
        # Look through PACKAGE_ARCHS for the priority order?
        if pkgarch and pkgarch == mach_arch:
            multiarch = mach_arch
            break

    bb.data.setVar('MULTIMACH_ARCH', multiarch, d)
}

def check_gcc3(data):

	gcc3_versions = 'gcc-3.4.6 gcc-3.4.7 gcc-3.4 gcc34 gcc-3.4.4 gcc-3.3 gcc33 gcc-3.3.6 gcc-3.2 gcc32'

	for gcc3 in gcc3_versions.split():
		if check_app_exists(gcc3, data):
			return gcc3
	
	return False

addtask cleanall after do_clean
python do_cleanall() {
        sstate_clean_cachefiles(d)

        src_uri = (bb.data.getVar('SRC_URI', d, True) or "").split()
        if len(src_uri) == 0:
            return

	localdata = bb.data.createCopy(d)
	bb.data.update_data(localdata)

        try:
            fetcher = bb.fetch2.Fetch(src_uri, localdata)
            fetcher.clean()
        except bb.fetch2.BBFetchException, e:
            raise bb.build.FuncFailed(e)
}
do_cleanall[nostamp] = "1"


EXPORT_FUNCTIONS do_fetch do_unpack do_configure do_compile do_install do_package
