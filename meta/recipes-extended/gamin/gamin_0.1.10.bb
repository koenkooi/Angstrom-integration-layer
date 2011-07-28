SUMMARY = "Gamin the File Alteration Monitor"
DESCRIPTION = "Gamin is a file and directory monitoring system defined to \
be a subset of the FAM (File Alteration Monitor) system."
HOMEPAGE = "http://people.gnome.org/~veillard/gamin/"

LICENSE = "LGPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=412a9be54757a155d0b997b52b519f62"

DEPENDS = "glib-2.0"
PROVIDES = "fam"
PR = "r3"

SRC_URI = "http://www.gnome.org/~veillard/gamin/sources/gamin-${PV}.tar.gz \
           file://no-abstract-sockets.patch"

SRC_URI[md5sum] = "b4ec549e57da470c04edd5ec2876a028"
SRC_URI[sha256sum] = "28085f0ae8be10eab582ff186af4fb0be92cc6c62b5cc19cd09b295c7c2899a1"

inherit autotools pkgconfig

EXTRA_OECONF = "--without-python"

PACKAGES += "lib${PN} lib${PN}-dev"
FILES_${PN} = "${libexecdir}"
FILES_${PN}-dbg += "${libexecdir}/.debug"
FILES_lib${PN} = "${libdir}/lib*.so.*"
FILES_lib${PN}-dev = "${includedir} ${libdir}/pkgconfig ${libdir}/lib*.la \
                      ${libdir}/lib*.a ${libdir}/lib*.so"

RDEPENDS_lib${PN} = "${PN}"

LEAD_SONAME = "libgamin-1.so"

