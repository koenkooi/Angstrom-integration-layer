require opkg_svn.bb

DEPENDS = "curl"
PROVIDES += "opkg"

EXTRA_OECONF += "--disable-gpg"

DEFAULT_PREFERENCE = "-1"
