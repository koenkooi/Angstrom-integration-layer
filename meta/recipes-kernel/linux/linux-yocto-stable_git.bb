inherit kernel
require linux-yocto.inc

KMACHINE = "common_pc"
KMACHINE_qemux86  = "common_pc"
KMACHINE_qemux86-64  = "common_pc_64"
KMACHINE_qemuppc  = "qemu_ppc32"
KMACHINE_qemumips = "mti_malta32_be"
KMACHINE_qemuarm  = "arm_versatile_926ejs"
KMACHINE_atom-pc  = "atom-pc"
KMACHINE_routerstationpro = "routerstationpro"
KMACHINE_mpc8315e-rdb = "fsl-mpc8315e-rdb"
KMACHINE_beagleboard = "beagleboard"

LINUX_VERSION ?= "2.6.34"
LINUX_VERSION_EXTENSION ?= "-yocto-${LINUX_KERNEL_TYPE_EXTENSION}"

KMETA = wrs_meta
KBRANCH = ${KMACHINE}-${LINUX_KERNEL_TYPE_EXTENSION}

PR = "r1"
PV = "${LINUX_VERSION}+git${SRCPV}"
SRCREV_FORMAT = "meta_machine"

COMPATIBLE_MACHINE = "(qemuarm|qemux86|qemuppc|qemumips|qemux86-64|atom-pc|routerstationpro|mpc8315e-rdb|beagleboard)"

# this performs a fixup on historical kernel types with embedded _'s
python __anonymous () {
    import bb, re, string

    kerntype = string.replace(bb.data.expand("${LINUX_KERNEL_TYPE}", d), "_", "-")
    bb.data.setVar("LINUX_KERNEL_TYPE_EXTENSION", kerntype, d)
}

SRC_URI = "git://git.yoctoproject.org/linux-yocto-2.6.34.git;protocol=git;nocheckout=1;branch=${KBRANCH},wrs_meta;name=machine,meta"

# Functionality flags
KERNEL_REVISION_CHECKING ?= "t"
KERNEL_FEATURES=features/netfilter

# extra tasks
addtask kernel_link_vmlinux after do_compile before do_install
addtask validate_branches before do_patch after do_kernel_checkout

require linux-tools.inc
