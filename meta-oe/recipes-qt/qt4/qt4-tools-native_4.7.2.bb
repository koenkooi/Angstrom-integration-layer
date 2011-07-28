require qt4-tools-native.inc

PR = "${INC_PR}.0"

# Find the g++.conf/linux.conf in the right directory.
FILESPATHPKG =. "qt-${PV}:"

EXTRA_OECONF += " -no-fast -silent -no-rpath"

TOBUILD := "src/tools/bootstrap ${TOBUILD}"

SRC_URI[md5sum] = "66b992f5c21145df08c99d21847f4fdb"
SRC_URI[sha256sum] = "d4783b524b90bcd270ccf6e7a30d5fb51696c47eb5de49ebc2d553cd3eb49336"
