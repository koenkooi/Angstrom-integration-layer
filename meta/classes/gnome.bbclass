def gnome_verdir(v):
	import re
	m = re.match("^([0-9]+)\.([0-9]+)", v)
	return "%s.%s" % (m.group(1), m.group(2))

SECTION ?= "x11/gnome"
SRC_URI = "${GNOME_MIRROR}/${BPN}/${@gnome_verdir("${PV}")}/${BPN}-${PV}.tar.bz2;name=archive"

DEPENDS += "gnome-common"

FILES_${PN} += "${datadir}/application-registry \
    ${datadir}/mime-info \
    ${datadir}/gnome-2.0"

inherit autotools pkgconfig gconf

EXTRA_OEMAKE += "GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL=1"
