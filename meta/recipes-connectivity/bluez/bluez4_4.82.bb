SUMMARY = "Linux Bluetooth Stack Userland V4"
DESCRIPTION = "Linux Bluetooth stack V4 userland components.  These include a system configurations, daemons, tools and system libraries."
HOMEPAGE = "http://www.bluez.org"
SECTION = "libs"
PRIORITY = "optional"
LICENSE = "GPLv2+ & LGPLv2.1+"
LIC_FILES_CHKSUM = "file://COPYING;md5=12f884d2ae1ff87c09e5b7ccc2c4ca7e \
                    file://COPYING.LIB;md5=fb504b67c50331fc78734fed90fb0e09 \
                    file://src/main.c;beginline=1;endline=24;md5=9bc54b93cd7e17bf03f52513f39f926e \
                    file://sbc/sbc.c;beginline=1;endline=25;md5=1a40781ed30d50d8639323a184aeb191"
DEPENDS = "gst-plugins-base alsa-lib libusb dbus-glib libnl"
RDEPENDS_${PN}-dev = "bluez-hcidump"

# For angstrom we want this to replace at least bluez-libs
PROVIDES_append_angstrom = " bluez-utils bluez-libs"

ASNEEDED = ""

PR = "r0"

SRC_URI = "\
  ${KERNELORG_MIRROR}/linux/bluetooth/bluez-${PV}.tar.gz \
  file://fix-dfutool-usb-declaration-mismatch.patch;patch=1 \
  file://sbc-thumb.patch;patch=1 \
  file://bluetooth.conf \
"

SRC_URI[md5sum] = "b9e5de607e5e43c868c35c68fe6f189f"
SRC_URI[sha256sum] = "75dc506f5346e1eb803f44294ae02406e806e309d9c9bda1de7ed235ff794b6d"
S = "${WORKDIR}/bluez-${PV}"

inherit autotools

EXTRA_OECONF = "\
  --enable-gstreamer \
  --enable-alsa \
  --enable-usb \
  --enable-netlink \
  --enable-tools \
  --enable-bccmd \
  --enable-hid2hci \
  --enable-dfutool \
  --enable-hidd \
  --enable-pandd \
  --enable-dund \
  --disable-cups \
  --enable-test \
  --enable-manpages \
  --enable-configfiles \
  --enable-initscripts \
  --disable-pcmciarules \
"

do_install_append() {
	install -m 0644 ${S}/audio/audio.conf ${D}/${sysconfdir}/bluetooth/
	install -m 0644 ${S}/network/network.conf ${D}/${sysconfdir}/bluetooth/
	install -m 0644 ${S}/input/input.conf ${D}/${sysconfdir}/bluetooth/
	# at_console doesn't really work with the current state of OE, so punch some more holes so people can actually use BT
	install -m 0644 ${WORKDIR}/bluetooth.conf ${D}/${sysconfdir}/dbus-1/system.d/
}

PACKAGES =+ "gst-plugin-bluez libasound-module-bluez"

FILES_gst-plugin-bluez = "${libdir}/gstreamer-0.10/lib*.so"
FILES_libasound-module-bluez = "${libdir}/alsa-lib/lib*.so"
FILES_${PN} += "${libdir}/bluetooth/plugins/*.so"
FILES_${PN}-dev += "\
  ${libdir}/bluetooth/plugins/*.la \
  ${libdir}/alsa-lib/*.la \
  ${libdir}/gstreamer-0.10/*.la \
"

FILES_${PN}-dbg += "\
  ${libdir}/bluetooth/plugins/.debug \
  ${libdir}/*/.debug \
"
