DESCRIPTION = "gvfs is a userspace virtual filesystem"
LICENSE = "LGPLv2"
LIC_FILES_CHKSUM = "file://COPYING;md5=3bf50002aefd002f49e7bb854063f7e7"

DEPENDS = "gnome-keyring glib-2.0 fuse avahi fuse gconf"
# optional: gphoto2 obexftp libcdio libimobiledevice samba

inherit gnome
SRC_URI[archive.md5sum] = "402f94b187b197b403d25c85caeb9562"
SRC_URI[archive.sha256sum] = "0895ac8f6d416e1b15433b6b6b68eb119c6e8b04fdb66db665d684355ef89345"

EXTRA_OECONF = "--enable-samba  --with-archive-includes=${STAGING_INCDIR} --with-samba-includes=${STAGING_INCDIR}"

PACKAGES =+ "gvfsd-ftp gvfsd-sftp gvfsd-trash"

FILES_${PN} += "${datadir}/dbus-1/services/* ${datadir}/GConf ${datadir}/glib-2.0 ${libdir}/gio/modules/*.so"
FILES_${PN}-dbg += "${libdir}/gio/modules/.debug/*"
FILES_${PN}-dev += "${libdir}/gio/modules/*.la"

FILES_gvfsd-ftp = "${libexecdir}/gvfsd-ftp ${sysconfdir}/gvfs/mounts/ftp.mount"
FILES_gvfsd-sftp = "${libexecdir}/gvfsd-sftp ${sysconfdir}/gvfs/mounts/sftp.mount"
FILES_gvfsd-trash = "${libexecdir}/gvfsd-trash ${sysconfdir}/gvfs/mounts/trash.mount"

