SUMMARY = "Xt: X Toolkit Intrinsics library"

DESCRIPTION = "The Intrinsics are a programming library tailored to the \
special requirements of user interface construction within a network \
window system, specifically the X Window System. The Intrinsics and a \
widget set make up an X Toolkit. The Intrinsics provide the base \
mechanism necessary to build a wide variety of interoperating widget \
sets and application environments. The Intrinsics are a layer on top of \
Xlib, the C Library X Interface. They extend the fundamental \
abstractions provided by the X Window System while still remaining \
independent of any particular user interface policy or style."

require xorg-lib-common.inc

LICENSE = "MIT & MIT-style"
LIC_FILES_CHKSUM = "file://COPYING;md5=3239170e81427c5948287df07691f03f"


DEPENDS += "util-linux libxcb libsm virtual/libx11 kbproto libxdmcp"
PROVIDES = "xt"

PR = "r0"
PE = "1"

XORG_PN = "libXt"

BBCLASSEXTEND = "native"

EXTRA_OECONF += "--disable-install-makestrs --disable-xkb"

do_compile() {
	(
		unset CC LD CXX CCLD CFLAGS
		oe_runmake -C util 'XT_CFLAGS=' 'CC=${BUILD_CC}' 'LD=${BUILD_LD}' 'CXX=${BUILD_CXX}' 'CCLD=${BUILD_CCLD}' 'CFLAGS=-D_GNU_SOURCE -I${STAGING_INCDIR_NATIVE} ${BUILD_CFLAGS}' 'LDFLAGS=${BUILD_LDFLAGS}' 'CXXFLAGS=${BUILD_CXXFLAGS}' 'CPPFLAGS=${BUILD_CPPFLAGS}' makestrs
	)
	if [ "$?" != "0" ]; then
		exit 1
	fi
	oe_runmake
}

SRC_URI[md5sum] = "eb22c0a1f172b06b97a3f5ae89768412"
SRC_URI[sha256sum] = "a2a1c29c684e3c9082cdb920b5aea802b179d19107b9ab2170fda07575559da7"
