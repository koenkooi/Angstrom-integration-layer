LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/LICENSE;md5=3f40d7994397109285ec7b81fdeb3b58"

PV = "${DISTRO_VERSION}"
PR = "r9"
PE = "2"

SRC_URI = "file://lsb_release"

PACKAGES = "${PN}"
PACKAGE_ARCH = "${MACHINE_ARCH}"

do_install() {
	install -d ${D}${sysconfdir}
	echo "Angstrom ${DISTRO_VERSION} (Core edition)" > ${D}${sysconfdir}/angstrom-version
	echo "Built from branch: ${METADATA_BRANCH}" >> ${D}${sysconfdir}/angstrom-version
	echo "Revision: ${METADATA_REVISION}" >> ${D}${sysconfdir}/angstrom-version
	echo "Target system: ${TARGET_SYS}" >> ${D}${sysconfdir}/angstrom-version

	echo "NAME=Angstrom" > ${D}${sysconfdir}/os-release
	echo "ID=angstrom" >> ${D}${sysconfdir}/os-release
	echo "PRETTY_NAME=The Ångström Distribution" >> ${D}${sysconfdir}/os-release
	echo "ANSI_COLOR=1;35" >> ${D}${sysconfdir}/os-release
	
	install -d ${D}${bindir}
	install -m 0755 ${WORKDIR}/lsb_release ${D}${bindir}/
}
