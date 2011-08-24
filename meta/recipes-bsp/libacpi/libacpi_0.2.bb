SUMMARY = "ACPI data gathering library."
DESCRIPTION = "General purpose shared library for programs gathering ACPI data on Linux. \
Thermal zones, battery infomration, fan information and AC states are implemented."
SECTION = "base"
HOMEPAGE = "http://www.ngolde.de/libacpi.html"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=fec17f82f16630adf2dfb7d2a46f21c5"
PR = "r2"

SRC_URI = "http://www.ngolde.de/download/libacpi-${PV}.tar.gz \
	   file://makefile-fix.patch "

SRC_URI[md5sum] = "05b53dd7bead66dda35fec502b91066c"
SRC_URI[sha256sum] = "13086e31d428b9c125954d48ac497b754bbbce2ef34ea29ecd903e82e25bad29"

PACKAGES += "${PN}-bin"

FILES_${PN} = "${libdir}/libacpi.so.*"
FILES_${PN}-bin = "${bindir}"

COMPATIBLE_HOST = '(x86_64|i.86).*-(linux|freebsd.*)'

CFLAGS += "-fPIC"

do_install() {
	oe_runmake install DESTDIR=${D} PREFIX=${exec_prefix}
}
