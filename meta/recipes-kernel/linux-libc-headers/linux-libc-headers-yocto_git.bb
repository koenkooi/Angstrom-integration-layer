require linux-libc-headers.inc
include recipes-kernel/linux/linux-yocto.inc

B = "${S}"

INHIBIT_DEFAULT_DEPS = "1"
DEPENDS += "unifdef-native"
PROVIDES = "linux-libc-headers"
RPROVIDES_${PN}-dev = "linux-libc-headers-dev"
RPROVIDES_${PN}-dbg = "linux-libc-headers-dbg"
SRCREV = "69cfbdf9f1ff461a75e5b77d6d7ba35e97db4cc3"
PV = "2.6.37+git-${SRCPV}"
PR = "r4"

SRCREV_FORMAT = "meta_machine"
SRC_URI = "git://git.yoctoproject.org/linux-yocto-2.6.37;protocol=git;nocheckout=1;branch=${KBRANCH},meta;name=machine,meta"

# force this to empty to prevent installation failures, we aren't
# building a device tree as part of kern headers
KERNEL_DEVICETREE=

set_arch() {
	case ${TARGET_ARCH} in
		arm*)     ARCH=arm ;;
		i*86*)    ARCH=i386 ;;
		ia64*)    ARCH=ia64 ;;
		mips*)    ARCH=mips ;;
		powerpc*) ARCH=powerpc ;;
		x86_64*)  ARCH=x86_64 ;;
	esac
}

do_configure() {
	set_arch
	oe_runmake allnoconfig ARCH=$ARCH
}

do_kernel_configme() {
}

do_patch () {
}

do_compile () {
}

do_install() {
	set_arch
	oe_runmake headers_install INSTALL_HDR_PATH=${D}${exec_prefix} ARCH=$ARCH

        # The ..install.cmd conflicts between various configure runs
        find ${D}${includedir} -name ..install.cmd | xargs rm -f
}

BBCLASSEXTEND = "nativesdk"
