SUMMARY = "The basic file, shell and text manipulation utilities."
DESCRIPTION = "The GNU Core Utilities provide the basic file, shell and text \
manipulation utilities. These are the core utilities which are expected to exist on \
every system."
HOMEPAGE = "http://www.gnu.org/software/coreutils/"
BUGTRACKER = "http://debbugs.gnu.org/coreutils"
LICENSE = "GPLv3+"
LIC_FILES_CHKSUM = "file://COPYING;md5=d32239bcb673463ab874e80d47fae504\
                    file://src/ls.c;startline=5;endline=16;md5=e1a509558876db58fb6667ba140137ad"
PR = "r1"
DEPENDS = "perl-native gmp"
DEPENDS_virtclass-native = "perl-native"

inherit autotools gettext

SRC_URI = "${GNU_MIRROR}/coreutils/${BP}.tar.gz"

SRC_URI[md5sum] = "36909ae68840d73a800120cf74af794a"
SRC_URI[sha256sum] = "aa991fa4296b22ff929a31a5cb5528bb783c84cdef4503c4ff311cfbeaebf50a"

EXTRA_OECONF_virtclass-native = "--without-gmp"

# [ gets a special treatment and is not included in this
bindir_progs = "base64 basename chcon cksum comm csplit cut dir dircolors dirname du \
                env expand expr factor fmt fold groups head hostid id install \
                join link logname md5sum mkfifo mktemp nice nl nohup nproc od paste pathchk \
                pinky pr printenv printf ptx readlink runcon seq sha1sum sha224sum sha256sum \
                sha384sum sha512sum shred shuf sort split stat stdbuf sum tac tail tee test timeout\
                tr truncate tsort tty unexpand uniq unlink uptime users vdir wc who whoami yes"

# hostname gets a special treatment and is not included in this
base_bindir_progs = "cat chgrp chmod chown cp date dd echo false kill ln ls mkdir \
                     mknod mv pwd rm rmdir sleep stty sync touch true uname"

sbindir_progs= "chroot"

do_install_append() {
	for i in ${bindir_progs}; do mv ${D}${bindir}/$i ${D}${bindir}/$i.${PN}; done

	install -d ${D}${base_bindir}
	for i in ${base_bindir_progs}; do mv ${D}${bindir}/$i ${D}${base_bindir}/$i.${PN}; done

	install -d ${D}${sbindir}
	for i in ${sbindir_progs}; do mv ${D}${bindir}/$i ${D}${sbindir}/$i.${PN}; done

	# [ requires special handling because [.coreutils will cause the sed stuff
	# in update-alternatives to fail, therefore use lbracket - the name used
	# for the actual source file.
	mv ${D}${bindir}/[ ${D}${bindir}/lbracket.${PN}
}

pkg_postinst_${PN} () {
	for i in ${bindir_progs}; do update-alternatives --install ${bindir}/$i $i $i.${PN} 100; done

	for i in ${base_bindir_progs}; do update-alternatives --install ${base_bindir}/$i $i $i.${PN} 100; done

	for i in ${sbindir_progs}; do update-alternatives --install ${sbindir}/$i $i $i.${PN} 100; done

	# Special cases. [ needs to be treated separately.
	update-alternatives --install '${bindir}/[' '[' 'lbracket.${PN}' 100
}

pkg_prerm_${PN} () {
	for i in ${bindir_progs}; do update-alternatives --remove $i $i.${PN}; done

	for i in ${base_bindir_progs}; do update-alternatives --remove $i $i.${PN}; done

	for i in ${sbindir_progs}; do update-alternatives --remove $i $i.${PN}; done

	# The special cases
	update-alternatives --remove hostname hostname.${PN}
	update-alternatives --remove uptime uptime.${PN}
	update-alternatives --remove '[' 'lbracket.${PN}'
}

BBCLASSEXTEND = "native"
