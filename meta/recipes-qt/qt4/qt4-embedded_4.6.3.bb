require qt-${PV}.inc
require qt4-embedded.inc

SRC_URI += "file://qthelp-lib-qtclucene.patch"

PR = "${INC_PR}.2"

QT_CONFIG_FLAGS_append_armv6 = " -no-neon "

