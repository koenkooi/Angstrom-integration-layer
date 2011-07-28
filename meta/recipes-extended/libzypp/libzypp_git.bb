HOMEPAGE = "http://en.opensue.org/Portal:Libzypp"
DESCRIPTION  = "The ZYpp Linux Software management framework"

LICENSE  = "GPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=11fccc94d26293d78cb4996cb17e5fa7"

inherit cmake

DEPENDS  = "rpm boost gettext curl libxml2 zlib sat-solver expat openssl udev"

# rpmdb2solv from sat-solver is run from libzypp
RDEPENDS_${PN} = "sat-solver"

S = "${WORKDIR}/git"
PV = "0.0-git${SRCPV}"
PR = "r8"

SRC_URI = "git://gitorious.org/opensuse/libzypp.git;protocol=git \
           file://no-doc.patch \
           file://rpm5.patch \
           file://rpm5-no-rpmdbinit.patch \
           file://builtin-arch.patch;apply=no \
           file://no-builtin-arch.patch;apply=no \
           file://archconf.patch;apply=no \
	   file://config-release.patch \
          "

SRC_URI_append_mips = " file://mips-workaround-gcc-tribool-error.patch"

FILES_${PN} += "${libdir}/zypp ${datadir}/zypp ${datadir}/icons"
FILES_${PN}-dev += "${datadir}/cmake"

EXTRA_OECMAKE += "-DLIB=lib"

PACKAGE_ARCH = "${MACHINE_ARCH}"

do_archpatch () {
	PKG_ARCH_TAIL=`sed -n ${S}/zypp/Arch.cc -e "s|^.*defCompatibleWith( _${BASE_PACKAGE_ARCH},[ \t]*\(.*\) .*$|\1|p"`
	if [ "x${PKG_ARCH_TAIL}" == x ]; then
		PATCHFILE=${WORKDIR}/no-builtin-arch.patch
	else
		PATCHFILE=${WORKDIR}/builtin-arch.patch
	fi

	sed -i "${PATCHFILE}" \
		-e "s|@MACHINE_ARCH@|${MACHINE_ARCH}|g" \
		-e "s|@PKG_ARCH@|${BASE_PACKAGE_ARCH}|g" \
		-e "s|@PKG_ARCH_TAIL@|${PKG_ARCH_TAIL}|g"

	patch -p1 -i "${PATCHFILE}"

	sed -i ${WORKDIR}/archconf.patch -e "s|@MACHINE_ARCH@|${MACHINE_ARCH}|g"
	patch -p1 -i ${WORKDIR}/archconf.patch
}

addtask archpatch before do_patch after do_unpack
