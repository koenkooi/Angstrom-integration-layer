require recipes-core/images/poky-image-directdisk.inc

DESCRIPTION = "Sato Direct Disk Image"

LICENSE = "MIT"

ROOTFS = "${DEPLOY_DIR_IMAGE}/poky-image-sato-${MACHINE}.ext3"

do_bootdirectdisk[depends] += "poky-image-sato:do_rootfs"
