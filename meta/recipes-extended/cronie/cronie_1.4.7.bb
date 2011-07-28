SUMMARY = "Cron daemon for executing programs at set times"
DESCRIPTION = "Cronie contains the standard UNIX daemon crond that runs \
specified programs at scheduled times and related tools. It is based on the \
original cron and has security and configuration enhancements like the \
ability to use pam and SELinux."
HOMEPAGE = "https://fedorahosted.org/cronie/"
BUGTRACKER = "mmaslano@redhat.com"

# Internet Systems Consortium License
LICENSE = "ISC & BSD"
LIC_FILES_CHKSUM = "file://COPYING;md5=963ea0772a2adbdcd607a9b2ec320c11 \
                    file://src/cron.h;endline=20;md5=b425c334265026177128353a142633b4 \
                    file://src/popen.c;beginline=3;endline=31;md5=edd50742d8def712e9472dba353668a9"

SECTION = "utils"

PR = "r2"

SRC_URI = "https://fedorahosted.org/releases/c/r/cronie/cronie-${PV}.tar.gz \
           file://crond.init \
           file://crontab"

SRC_URI[md5sum] = "dfc26c47756d0c40ee27ae3c7ee98e0d"
SRC_URI[sha256sum] = "83bae15ae5504454ba74f4142f5db3aa22be594327fea19d2534f65803137fbd"

inherit autotools update-rc.d

INITSCRIPT_NAME = "crond"
INITSCRIPT_PARAMS = "start 90 2 3 4 5 . stop 60 0 1 6 ."

do_install_append () {
	install -d ${D}${sysconfdir}/sysconfig/
	install -d ${D}${sysconfdir}/init.d/
	install -m 0644 ${S}/crond.sysconfig ${D}${sysconfdir}/sysconfig/crond
	install -m 0755 ${WORKDIR}/crond.init ${D}${sysconfdir}/init.d/crond

	# below are necessary for a complete cron environment
	install -d ${D}${localstatedir}/spool/cron
	install -m 0755 ${WORKDIR}/crontab ${D}${sysconfdir}/
	mkdir -p ${D}${sysconfdir}/cron.d
	mkdir -p ${D}${sysconfdir}/cron.hourly
	mkdir -p ${D}${sysconfdir}/cron.daily
	mkdir -p ${D}${sysconfdir}/cron.weekly
	mkdir -p ${D}${sysconfdir}/cron.monthly
}

FILES_${PN} += "${sysconfdir}/cron*"

pkg_postinst_${PN} () {
	if [ "x$D" != "x" ] ; then
		exit 1
	fi

	# below setting is necessary to allow normal user using crontab

	# add 'crontab' group and setgid for crontab binary
	grep crontab /etc/group || addgroup crontab
	chown root:crontab /usr/bin/crontab
	chmod 2755 /usr/bin/crontab

	# allow 'crontab' group write to /var/spool/cron
	chown root:crontab /var/spool/cron
	chmod 770 /var/spool/cron

	chmod 600 /etc/crontab
}
