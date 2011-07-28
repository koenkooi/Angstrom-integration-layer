SUMMARY = "Base system master password/group files."
DESCRIPTION = "The master copies of the user database files (/etc/passwd and /etc/group).  The update-passwd tool is also provided to keep the system databases synchronized with these master files."
SECTION = "base"
PR = "r2"
LICENSE = "GPLv2+"
LIC_FILES_CHKSUM = "file://COPYING;md5=eb723b61539feef013de476e68b5c50a"

SRC_URI = "${DEBIAN_MIRROR}/main/b/base-passwd/base-passwd_${PV}.tar.gz \
           file://nobash.patch \
           file://root-home.patch \
           file://login.defs"

SRC_URI[md5sum] = "47f22ab6b572d0133409ff6ad1fab402"
SRC_URI[sha256sum] = "d34acb35a9f9f221e7e4f642b9ef4b22083dd77bb2fc7216756f445316d842fc"

S = "${WORKDIR}/base-passwd"

inherit autotools

SSTATEPOSTINSTFUNCS += "base_passwd_sstate_postinst"

do_install () {
	install -d -m 755 ${D}${sbindir}
	install -p -m 755 update-passwd ${D}${sbindir}/
	install -d -m 755 ${D}${mandir}/man8 ${D}${mandir}/pl/man8
	install -p -m 644 man/update-passwd.8 ${D}${mandir}/man8/
	install -p -m 644 man/update-passwd.pl.8 \
		${D}${mandir}/pl/man8/update-passwd.8
	gzip -9 ${D}${mandir}/man8/* ${D}${mandir}/pl/man8/*
	install -d -m 755 ${D}${datadir}/base-passwd
	install -p -m 644 passwd.master ${D}${datadir}/base-passwd/
	install -p -m 644 group.master ${D}${datadir}/base-passwd/
	install -p -m 644 ${S}/../login.defs ${D}${datadir}/base-passwd/login.defs

	install -d -m 755 ${D}${docdir}/${PN}
	install -p -m 644 debian/changelog ${D}${docdir}/${PN}/
	gzip -9 ${D}${docdir}/${PN}/*
	install -p -m 644 README ${D}${docdir}/${PN}/
	install -p -m 644 debian/copyright ${D}${docdir}/${PN}/
}

pkg_postinst_${PN} () {
	set -e

	if [ ! -e $D${sysconfdir}/passwd ] ; then
		cp $D${datadir}/base-passwd/passwd.master $D${sysconfdir}/passwd
	fi

	if [ ! -e $D${sysconfdir}/group ] ; then
		cp $D${datadir}/base-passwd/group.master $D${sysconfdir}/group
	fi

	if [ ! -e $D{sysconfdir}/login.defs ] ; then
		cp $D${datadir}/base-passwd/login.defs $D${sysconfdir}/login.defs
	fi
	exit 0
}

base_passwd_sstate_postinst() {
	if [ "${BB_CURRENTTASK}" = "populate_sysroot" -o "${BB_CURRENTTASK}" = "populate_sysroot_setscene" ]
	then
		# Staging does not copy ${sysconfdir} files into the
		# target sysroot, so we need to do so manually. We
		# put these files in the target sysroot so they can
		# be used by recipes which use custom user/group
		# permissions.
		install -d -m 755 ${STAGING_DIR_TARGET}${sysconfdir}
		install -p -m 644 ${STAGING_DIR_TARGET}${datadir}/base-passwd/passwd.master ${STAGING_DIR_TARGET}${sysconfdir}/passwd
		install -p -m 644 ${STAGING_DIR_TARGET}${datadir}/base-passwd/group.master ${STAGING_DIR_TARGET}${sysconfdir}/group
		install -p -m 644 ${STAGING_DIR_TARGET}${datadir}/base-passwd/login.defs ${STAGING_DIR_TARGET}/${sysconfdir}/login.defs
	fi
}
