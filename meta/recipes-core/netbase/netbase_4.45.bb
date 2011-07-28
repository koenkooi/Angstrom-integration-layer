SUMMARY = "Basic TCP/IP networking support"
DESCRIPTION = "This package provides the necessary infrastructure for basic TCP/IP based networking"
HOMEPAGE = "http://packages.debian.org/netbase"
SECTION = "base"
LICENSE = "GPLv2"
LIC_FILES_CHKSUM = "file://debian/copyright;md5=3dd6192d306f582dee7687da3d8748ab"
PR = "r1"

inherit update-rc.d

INITSCRIPT_NAME = "networking"
INITSCRIPT_PARAMS = "start 40 S . stop 40 0 6 1 ."

SRC_URI = "${DEBIAN_MIRROR}/main/n/netbase/netbase_${PV}.tar.gz \
           file://init \
           file://hosts \
           file://interfaces \
           file://nfsroot"

do_install () {
	install -d ${D}${sysconfdir}/init.d \
		   ${D}${sbindir} \
		   ${D}${mandir}/man8 \
		   ${D}${sysconfdir}/network/if-pre-up.d \
		   ${D}${sysconfdir}/network/if-up.d \
		   ${D}${sysconfdir}/network/if-down.d \
		   ${D}${sysconfdir}/network/if-post-down.d
	install -m 0755 ${WORKDIR}/init ${D}${sysconfdir}/init.d/networking
	install -m 0644 ${WORKDIR}/hosts ${D}${sysconfdir}/hosts
	install -m 0644 etc-rpc ${D}${sysconfdir}/rpc
	install -m 0644 etc-protocols ${D}${sysconfdir}/protocols
	install -m 0644 etc-services ${D}${sysconfdir}/services
	install -m 0644 ${WORKDIR}/interfaces ${D}${sysconfdir}/network/interfaces
	install -m 0755 ${WORKDIR}/nfsroot ${D}${sysconfdir}/network/if-pre-up.d

	# Disable network manager on machines that commonly do NFS booting
	case "${MACHINE}" in
		"qemuarm" | "qemux86" | "qemux86-64" | "qemumips" | "qemuppc" )
			touch ${D}${sysconfdir}/network/nm-disabled-eth0
			;;
		*)
			;;
	esac
}

CONFFILES_${PN} = "${sysconfdir}/hosts ${sysconfdir}/network/interfaces"

PACKAGE_ARCH_qemuarm = "${MACHINE_ARCH}"
PACKAGE_ARCH_qemux86 = "${MACHINE_ARCH}"
PACKAGE_ARCH_qemux86-64 = "${MACHINE_ARCH}"

SRC_URI[md5sum] = "a56cb362ece358a5b3b8972e5c7be534"
SRC_URI[sha256sum] = "dea29d60b3d751f0c5669b5299af312ad269c48e6440e0072d0d68d9544ebad3"
