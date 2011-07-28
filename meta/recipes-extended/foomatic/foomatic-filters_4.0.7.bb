SUMMARY = "OpenPrinting printer support - filters"
DESCRIPTION = "Foomatic is a printer database designed to make it easier to set up \
common printers for use with UNIX-like operating systems.\
It provides the "glue" between a print spooler (like CUPS or lpr) and \
the printer, by processing files sent to the printer. \
 \
This package consists of filters used by the printer spoolers \
to convert the incoming PostScript data into the printer's native \
format using a printer-specific, but spooler-independent PPD file. \
"

DEPENDS += "cups perl libxml2"
PR = "r1"

LICENSE = "GPLv2+"
LIC_FILES_CHKSUM = "file://${WORKDIR}/foomatic-filters-${PV}/COPYING;md5=393a5ca445f6965873eca0259a17f833"

SRC_URI = "http://www.openprinting.org/download/foomatic/foomatic-filters-${PV}.tar.gz"

SRC_URI[md5sum] = "20abd25c1c98b2dae68709062a132a7d"
SRC_URI[sha256sum] = "090313fae40b177f505d9c9b93d7a4d7188b6d5d18b6ae41ab24903ac983478d"

do_install_append_linuxstdbase() {
    install -d ${D}${libdir}/cups/filter
    ln -sf ${bindir}/foomatic-rip ${D}${libdir}/cups/filter
}

FILES_${PN}_append_linuxstdbase += "${libdir}/cups/filter/foomatic-rip"

inherit autotools
