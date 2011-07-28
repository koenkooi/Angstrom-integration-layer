SUMMARY = "GPS Multiplexing Daemon"
DESCRIPTION = "Gypsy is a GPS multiplexing daemon which allows \
multiple clients to access GPS data from multiple GPS sources \
concurrently.  Gypsy also hides the details of parsing NMEA from the \
client applications, passing the data as simple values for the clients \
to use."
LICENSE = "GPLv2+ & LGPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=751419260aa954499f7abaabaa882bbe \
                    file://COPYING.lib;md5=7fbc338309ac38fefcd64b04bb903e34 \
                    file://src/main.c;beginline=1;endline=25;md5=3fe64e27e61b289b77383a54a982cbdd \
                    file://gypsy/gypsy-time.h;beginline=1;endline=24;md5=06432ea19a7b6607428d04d9dadc37fd"

SECTION = "x11"
DEPENDS = "glib-2.0 dbus bluez4 dbus-glib libxslt"

SRC_URI = "http://gypsy.freedesktop.org/releases/gypsy-${PV}.tar.gz \
           file://fix-unused-but-set-variable-warning.patch \
          "
PR = "r1"

inherit autotools pkgconfig

FILES_${PN} += "/usr/share/dbus-1/services/"

SRC_URI[md5sum] = "32b8db24db86d2dac87b391dd255f4bf"
SRC_URI[sha256sum] = "1986a58189614a950725c3bc7d05faa3b84695f35cb696326f340ef87fc3acaa"
