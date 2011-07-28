DESCRIPTION = "The Illume Windowing Environment -- install this task to get the Enlightenment Window Manager + the Illume environment."
SECTION = "x11/wm"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${TOPDIR}/meta-openembedded/meta-efl/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"
PV = "1.0"
PR = "r1"

# WORK IN PROGRESS

inherit task

# Default illume theme
ETHEME ?= "e-wm-theme-illume"
ECONFIG ?= "e-wm-config-illume2"

RDEPENDS_${PN} = "\
  task-x11-server \
  task-x11-utils \
  \
  e-wm \
  ${ECONFIG} \
  ${ETHEME} \
"
