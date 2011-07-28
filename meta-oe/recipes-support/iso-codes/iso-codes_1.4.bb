LICENSE = "LGPLv2.1"
LIC_FILES_CHKSUM = "file://LGPL-2.1;md5=fbc093901857fcd118f065f900982c24"

PACKAGE_ARCH = "all"
SRC_URI = "ftp://pkg-isocodes.alioth.debian.org/pub/pkg-isocodes/iso-codes-${PV}.tar.bz2"
SRC_URI[md5sum] = "4073466e57df23d39721513219e4f7ae"
SRC_URI[sha256sum] = "0a7cf177c25b3f0d77c60a5f1149aab9e03ba70f69bac70138a867efe19a1d97"

inherit autotools

FILES_${PN} += "${datadir}/xml/"
PACKAGE_ARCH = "all"

