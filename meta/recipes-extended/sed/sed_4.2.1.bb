DESCRIPTION = "sed is a Stream EDitor."
HOMEPAGE = "http://www.gnu.org/software/sed/"
LICENSE = "GPLv3+"
LIC_FILES_CHKSUM = "file://COPYING;md5=f27defe1e96c2e1ecd4e0c9be8967949 \
                    file://sed/sed.h;beginline=1;endline=17;md5=767ab3a06d7584f6fd0469abaec4412f"
SECTION = "console/utils"
PR = "r1"

SRC_URI = "${GNU_MIRROR}/sed/sed-${PV}.tar.gz"

SRC_URI[md5sum] = "f0fd4d7da574d4707e442285fd2d3b86"
SRC_URI[sha256sum] = "8773541ce097fdc4c5b9e7da12a82dffbb30cd91f7bc169f52f05f93b7fc3060"

inherit autotools update-alternatives gettext

do_install () {
	autotools_do_install
	install -d ${D}${base_bindir}
	mv ${D}${bindir}/sed ${D}${base_bindir}/sed.${PN}
}

ALTERNATIVE_NAME = "sed"
ALTERNATIVE_PATH = "sed.${PN}"
ALTERNATIVE_LINK = "${base_bindir}/sed"
ALTERNATIVE_PRIORITY = "100"

BBCLASSEXTEND = "native"
