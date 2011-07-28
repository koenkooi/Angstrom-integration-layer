DESCRIPTION = "ConsoleKit is a framework for defining and tracking users, login sessions, and seats."
HOMEPAGE="http://www.freedesktop.org/wiki/Software/ConsoleKit"
BUGTRACKER="https://bugs.freedesktop.org/buglist.cgi?query_format=specific&product=ConsoleKit"

LICENSE = "GPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=59530bdf33659b29e73d4adb9f9f6552 \
                    file://src/main.c;endline=21;md5=0a994e09769780220163255d8f9071c3"

DEPENDS = "dbus"

inherit gnome

SRC_URI = "http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-${PV}.tar.bz2 \
           file://nopolkit.patch"
SRC_URI[md5sum] = "f2657f93761206922d558471a936fbc3"
SRC_URI[sha256sum] = "43e0780c53078e125efcec3f847e484dc3533e49b408ce6a0ab1b223686b9c38"


S = "${WORKDIR}/ConsoleKit-${PV}"

EXTRA_OECONF = "--with-systemdsystemunitdir=${base_libdir}/systemd/system/"

FILES_${PN} += "${libdir}/ConsoleKit ${base_libdir} ${datadir}/dbus-1 ${datadir}/PolicyKit"


