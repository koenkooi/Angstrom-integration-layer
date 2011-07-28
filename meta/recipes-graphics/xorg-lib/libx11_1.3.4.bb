require libx11.inc
inherit gettext

LICENSE = "MIT & MIT-style & BSD"
LIC_FILES_CHKSUM = "file://COPYING;md5=bf75bfe4d05068311b5e6862d4b5f2c5"

PE = "1"
PR = "r4"

SRC_URI += "file://x11_disable_makekeys.patch \
            file://nodolt.patch \
            file://include_fix.patch \
	    file://makekeys_crosscompile.patch"

SRC_URI[md5sum] = "f65c9c7ecbfb64c19dbd7927160d63fd"
SRC_URI[sha256sum] = "88d7238ce5f7cd123450567de7a3b56a43556e4ccc45df38b8324147c889a844"

DEPENDS += "bigreqsproto xproto xextproto xtrans libxau xcmiscproto \
            libxdmcp xf86bigfontproto kbproto inputproto xproto-native libxcb"

DEPENDS_virtclass-native += "bigreqsproto-native xextproto-native \
            xtrans-native libxau-native xcmiscproto-native \
            libxdmcp-native xf86bigfontproto-native kbproto-native \
            inputproto-native xproto-native"

DEPENDS_virtclass-nativesdk += "bigreqsproto xproto xextproto \
            xtrans libxau xcmiscproto libxdmcp xf86bigfontproto kbproto \
            inputproto xproto-native"

XCB = "--with-xcb"
XCB_virtclass-native = "--without-xcb"
XCB_virtclass-nativesdk = "--without-xcb"
EXTRA_OECONF += "${XCB}"

BBCLASSEXTEND = "native nativesdk"
