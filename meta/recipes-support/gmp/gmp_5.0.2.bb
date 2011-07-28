require gmp.inc
LICENSE="LGPLv3&GPLv3"
LIC_FILES_CHKSUM = "file://COPYING;md5=d32239bcb673463ab874e80d47fae504 \
		    file://version.c;endline=18;md5=d8c56b52b9092346b9f93b4da65ef790"
PR = "r0"

SRC_URI_append += "file://sh4-asmfix.patch \
                   file://use-includedir.patch "


SRC_URI[md5sum] = "0bbaedc82fb30315b06b1588b9077cd3"
SRC_URI[sha256sum] = "dbc2db76fdd4e99f85d5e35aa378ed62c283e0d586b91bd8703aff75a7804c28"
