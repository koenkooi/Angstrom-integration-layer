DESCRIPTION = "Telepathy framework - Python package"
HOMEPAGE = "http://telepathy.freedesktop.org/wiki/"
LICENSE = "LGPLv2.1+"
LIC_FILES_CHKSUM = "file://COPYING;md5=2d5025d4aa3495befef8f17206a5b0a1 \
                    file://src/utils.py;beginline=1;endline=17;md5=9a07d1a9791a7429a14e7b25c6c86822"

RDEPENDS_${PN} += "python-dbus"

SRC_URI = "http://telepathy.freedesktop.org/releases/${BPN}/${P}.tar.gz \
           file://parallel_make.patch"

PR = "r1"

inherit autotools

SRC_URI[md5sum] = "f7ca25ab3c88874015b7e9728f7f3017"
SRC_URI[sha256sum] = "244c0e1bf4bbd78ae298ea659fe10bf3a73738db550156767cc2477aedf72376"

FILES_${PN} += "\
    ${libdir}/python*/site-packages/telepathy/*.py \
    ${libdir}/python*/site-packages/telepathy/*/*.py \
    "
