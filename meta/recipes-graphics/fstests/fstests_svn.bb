DESCRIPTION = "Various benchmarning tests for X"
HOMEPAGE = "http://www.o-hand.com"
SECTION = "devel"
LICENSE = "ZLIB"
DEPENDS = "pango libxext libxft virtual/libx11 gtk+"

SRCREV = "426"
PV = "0.0+svnr${SRCPV}"
PR = "r1"

inherit autotools

SRC_URI = "svn://svn.o-hand.com/repos/misc/trunk;module=fstests;proto=http \
	file://dso_linking_change_build_fix.patch"

S = "${WORKDIR}/fstests/tests"

do_install() {
    install -d ${D}${bindir}
    find . -name "test-*" -type f -perm -755 -exec install -m 0755 {} ${D}${bindir} \;   
}


LIC_FILES_CHKSUM = "file://test-pango-gdk.c;endline=24;md5=1ee74ec851ecda57eb7ac6cc180f7655"
