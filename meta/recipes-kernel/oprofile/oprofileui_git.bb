require oprofileui.inc

PV = "0.0+git${SRCPV}"
PR = "r4"

S = "${WORKDIR}/git"

# Oprofileui at http://labs.o-hand.com/oprofileui/ is not maintained now.
SRC_URI = "git://git.yoctoproject.org/oprofileui;protocol=git \
           file://dso_linking_change_build_fix.patch "
