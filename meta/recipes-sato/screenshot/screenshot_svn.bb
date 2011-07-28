DESCRIPTION = "An ultra-simple screen capture utility, aimed at handheld devices"
HOMEPAGE = "http://www.o-hand.com"
BUGTRACKER = "http://bugzilla.openedhand.com/"

LICENSE = "GPLv2 & GPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=94d55d512a9ba36caa9b7df079bae19f \
                    file://main.c;endline=9;md5=023e14d6404d0a961eb97cbd011fc141 \
                    file://screenshot-ui.h;endline=9;md5=638d9ffa83e9325a36df224166ed6ad0"

DEPENDS = "matchbox-panel-2"
SRCREV = "292"
PV = "0.0+svnr${SRCPV}"
PR = "r2"

SRC_URI = "svn://svn.o-hand.com/repos/misc/trunk;module=${BPN};proto=http \
           file://fix_ldadd_order.patch"

S = ${WORKDIR}/${PN}

inherit autotools pkgconfig

FILES_${PN} += "${libdir}/matchbox-panel/*.so"
FILES_${PN}-dbg += "${libdir}/matchbox-panel/.debug"
