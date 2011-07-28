SUMMARY = "Linux Trace Toolkit Viewer"
DESCRIPTION = "The Linux trace toolkit is a suite of tools designed to \
extract program execution details from the Linux operating system and  \
interpret them."
HOMEPAGE = "http://lttng.org/content/download"
BUGTRACKER = "n/a"

LICENSE = "GPLv2 & LGPLv2.1"
LIC_FILES_CHKSUM = "file://COPYING;md5=f650d5f5af1e9648fe0b40e290d3adbb \
                    file://ltt/ltt.h;beginline=2;endline=18;md5=8b7da9190028c50396d97fc85bad0da9 \
                    file://lttv/lttv/traceset.c;beginline=2;endline=17;md5=bcab42863b64b41d153bf81bbe2490a6"
PR = "r0"
DEPENDS = "gtk+ pango popt"

SECTION = "devel"

ALTNAME = "lttv-${PV}-21032011"

SRC_URI = "http://lttng.org/files/packages/${ALTNAME}.tar.gz"

SRC_URI[md5sum] = "071bf3dd13e7562c08ee8f8971cfc76d"
SRC_URI[sha256sum] = "cf87ffcf5d266b18979418e610a180a0b4214de41677f0be867885e15b2f7647"
S = "${WORKDIR}/${ALTNAME}"

inherit autotools

LEAD_SONAME = "liblttvtraceread*"

FILES_${PN} += "\
    ${libdir}/liblttvtraceread*.so \
    ${libdir}/lttv/plugins/*.so \
    ${datadir}/LinuxTraceToolkitViewer/facilities/* \
    ${datadir}/LinuxTraceToolkitViewer/pixmaps/* "
FILES_${PN}-dbg += "${libdir}/lttv/plugins/.debug/"

