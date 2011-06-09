require recipes-devtools/gcc/gcc-common.inc
ARM_INSTRUCTION_SET = "arm"

DEPENDS =+ "mpfr gmp libmpc elfutils"
NATIVEDEPS = "mpfr-native gmp-native gettext-native libmpc-native elfutils-native"

LICENSE="GCC RUNTIME LIBRARY EXCEPTION & GPLv2 & GPLv3 & LGPLv2.1 & LGPLv3"

LIC_FILES_CHKSUM = "file://COPYING;md5=59530bdf33659b29e73d4adb9f9f6552 \
                    file://COPYING3;md5=d32239bcb673463ab874e80d47fae504 \
                    file://COPYING3.LIB;md5=6a6a8e020838b23406c81b19c1d46df6 \
                    file://COPYING.LIB;md5=2d5025d4aa3495befef8f17206a5b0a1 \
                    file://COPYING.RUNTIME;md5=fe60d87048567d4fe8c8a0ed2448bcc8"


PV = "4.5"
INC_PR = "r36"
# BINV should  point to minor release 
BINV = "${PV}.3"

SRC_URI[md5sum] = "8e0b5c12212e185f3e4383106bfa9cc6"
SRC_URI[sha256sum] = "0a8847af44a9b33813b199997a73139517c96adfd519eaf24c79d4d9d09f65de"

SRC_URI = "${GNU_MIRROR}/gcc/gcc-${BINV}/gcc-${BINV}.tar.bz2 \
       file://gcc-4.3.1-ARCH_FLAGS_FOR_TARGET.patch \
       file://100-uclibc-conf.patch \
       file://gcc-uclibc-locale-ctype_touplow_t.patch \
       file://cache-amnesia.patch \
       file://gcc-flags-for-build.patch \
       file://libstdc++-emit-__cxa_end_cleanup-in-text.patch \
       file://Makefile.in.patch \
       file://gcc-armv4-pass-fix-v4bx-to-ld.patch \
       file://sh4-multilib.patch \
       file://arm-lib1funcs.as-fix-mismatch-between-conditions-of-an-IT-block.patch \
       \
       file://linaro/gcc-4.5-linaro-r99297.patch \
       file://linaro/gcc-4.5-linaro-r99298.patch \
       file://linaro/gcc-4.5-linaro-r99299.patch \
       file://linaro/gcc-4.5-linaro-r99300.patch \
       file://linaro/gcc-4.5-linaro-r99301.patch \
       file://linaro/gcc-4.5-linaro-r99302.patch \
       file://linaro/gcc-4.5-linaro-r99303.patch \
       file://linaro/gcc-4.5-linaro-r99304.patch \
       file://linaro/gcc-4.5-linaro-r99305.patch \
       file://linaro/gcc-4.5-linaro-r99306.patch \
       file://linaro/gcc-4.5-linaro-r99307.patch \
       file://linaro/gcc-4.5-linaro-r99308.patch \
       file://linaro/gcc-4.5-linaro-r99310.patch \
       file://linaro/gcc-4.5-linaro-r99312.patch \
       file://linaro/gcc-4.5-linaro-r99313.patch \
       file://linaro/gcc-4.5-linaro-r99314.patch \
       file://linaro/gcc-4.5-linaro-r99315.patch \
       file://linaro/gcc-4.5-linaro-r99316.patch \
       file://linaro/gcc-4.5-linaro-r99318.patch \
       file://linaro/gcc-4.5-linaro-r99319.patch \
       file://linaro/gcc-4.5-linaro-r99320.patch \
       file://linaro/gcc-4.5-linaro-r99321.patch \
       file://linaro/gcc-4.5-linaro-r99322.patch \
       file://linaro/gcc-4.5-linaro-r99323.patch \
       file://linaro/gcc-4.5-linaro-r99324.patch \
       file://linaro/gcc-4.5-linaro-r99325.patch \
       file://linaro/gcc-4.5-linaro-r99326.patch \
       file://linaro/gcc-4.5-linaro-r99327.patch \
       file://linaro/gcc-4.5-linaro-r99332.patch \
       file://linaro/gcc-4.5-linaro-r99335.patch \
       file://linaro/gcc-4.5-linaro-r99336.patch \
       file://linaro/gcc-4.5-linaro-r99337.patch \
       file://linaro/gcc-4.5-linaro-r99338.patch \
       file://linaro/gcc-4.5-linaro-r99339.patch \
       file://linaro/gcc-4.5-linaro-r99340.patch \
       file://linaro/gcc-4.5-linaro-r99341.patch \
       file://linaro/gcc-4.5-linaro-r99342.patch \
       file://linaro/gcc-4.5-linaro-r99343.patch \
       file://linaro/gcc-4.5-linaro-r99344.patch \
       file://linaro/gcc-4.5-linaro-r99345.patch \
       file://linaro/gcc-4.5-linaro-r99346.patch \
       file://linaro/gcc-4.5-linaro-r99347.patch \
       file://linaro/gcc-4.5-linaro-r99348.patch \
       file://linaro/gcc-4.5-linaro-r99349.patch \
       file://linaro/gcc-4.5-linaro-r99351.patch \
       file://linaro/gcc-4.5-linaro-r99352.patch \
       file://linaro/gcc-4.5-linaro-r99353.patch \
       file://linaro/gcc-4.5-linaro-r99354.patch \
       file://linaro/gcc-4.5-linaro-r99355.patch \
       file://linaro/gcc-4.5-linaro-r99356.patch \
       file://linaro/gcc-4.5-linaro-r99357.patch \
       file://linaro/gcc-4.5-linaro-r99358.patch \
       file://linaro/gcc-4.5-linaro-r99359.patch \
       file://linaro/gcc-4.5-linaro-r99360.patch \
       file://linaro/gcc-4.5-linaro-r99361.patch \
       file://linaro/gcc-4.5-linaro-r99363.patch \
       file://linaro/gcc-4.5-linaro-r99364.patch \
       file://linaro/gcc-4.5-linaro-r99365.patch \
       file://linaro/gcc-4.5-linaro-r99366.patch \
       file://linaro/gcc-4.5-linaro-r99367.patch \
       file://linaro/gcc-4.5-linaro-r99368.patch \
       file://linaro/gcc-4.5-linaro-r99369.patch \
       file://linaro/gcc-4.5-linaro-r99371.patch \
       file://linaro/gcc-4.5-linaro-r99372.patch \
       file://linaro/gcc-4.5-linaro-r99373.patch \
       file://linaro/gcc-4.5-linaro-r99374.patch \
       file://linaro/gcc-4.5-linaro-r99375.patch \
       file://linaro/gcc-4.5-linaro-r99376.patch \
       file://linaro/gcc-4.5-linaro-r99377.patch \
       file://linaro/gcc-4.5-linaro-r99378.patch \
       file://linaro/gcc-4.5-linaro-r99379.patch \
       file://linaro/gcc-4.5-linaro-r99380.patch \
       file://linaro/gcc-4.5-linaro-r99381.patch \
       file://linaro/gcc-4.5-linaro-r99383.patch \
       file://linaro/gcc-4.5-linaro-r99384.patch \
       file://linaro/gcc-4.5-linaro-r99385.patch \
       file://linaro/gcc-4.5-linaro-r99388.patch \
       file://linaro/gcc-4.5-linaro-r99391.patch \
       file://linaro/gcc-4.5-linaro-r99392.patch \
       file://linaro/gcc-4.5-linaro-r99393.patch \
       file://linaro/gcc-4.5-linaro-r99395.patch \
       file://linaro/gcc-4.5-linaro-r99396.patch \
       file://linaro/gcc-4.5-linaro-r99397.patch \
       file://linaro/gcc-4.5-linaro-r99398.patch \
       file://linaro/gcc-4.5-linaro-r99402.patch \
       file://linaro/gcc-4.5-linaro-r99403.patch \
       file://linaro/gcc-4.5-linaro-r99404.patch \
       file://linaro/gcc-4.5-linaro-r99405.patch \
       file://linaro/gcc-4.5-linaro-r99406.patch \
       file://linaro/gcc-4.5-linaro-r99407.patch \
       file://linaro/gcc-4.5-linaro-r99408.patch \
       file://linaro/gcc-4.5-linaro-r99409.patch \
       file://linaro/gcc-4.5-linaro-r99410.patch \
       file://linaro/gcc-4.5-linaro-r99411.patch \
       file://linaro/gcc-4.5-linaro-r99412.patch \
       file://linaro/gcc-4.5-linaro-r99413.patch \
       file://linaro/gcc-4.5-linaro-r99415.patch \
       file://linaro/gcc-4.5-linaro-r99416.patch \
       file://linaro/gcc-4.5-linaro-r99417.patch \
       file://linaro/gcc-4.5-linaro-r99418.patch \
       file://linaro/gcc-4.5-linaro-r99419.patch \
       file://linaro/gcc-4.5-linaro-r99420.patch \
       file://linaro/gcc-4.5-linaro-r99421.patch \
       file://linaro/gcc-4.5-linaro-r99423.patch \
       file://linaro/gcc-4.5-linaro-r99424.patch \
       file://linaro/gcc-4.5-linaro-r99425.patch \
       file://linaro/gcc-4.5-linaro-r99426.patch \
       file://linaro/gcc-4.5-linaro-r99429.patch \
       file://linaro/gcc-4.5-linaro-r99432.patch \
       file://linaro/gcc-4.5-linaro-r99433.patch \
       file://linaro/gcc-4.5-linaro-r99434.patch \
       file://linaro/gcc-4.5-linaro-r99435.patch \
       file://linaro/gcc-4.5-linaro-r99436.patch \
       file://linaro/gcc-4.5-linaro-r99437.patch \
       file://linaro/gcc-4.5-linaro-r99439.patch \
       file://linaro/gcc-4.5-linaro-r99440.patch \
       file://linaro/gcc-4.5-linaro-r99441.patch \
       file://linaro/gcc-4.5-linaro-r99442.patch \
       file://linaro/gcc-4.5-linaro-r99443.patch \
       file://linaro/gcc-4.5-linaro-r99444.patch \
       file://linaro/gcc-4.5-linaro-r99449.patch \
       file://linaro/gcc-4.5-linaro-r99450.patch \
       file://linaro/gcc-4.5-linaro-r99451.patch \
       file://linaro/gcc-4.5-linaro-r99452.patch \
       file://linaro/gcc-4.5-linaro-r99453.patch \
       file://linaro/gcc-4.5-linaro-r99454.patch \
       file://linaro/gcc-4.5-linaro-r99455.patch \
       file://linaro/gcc-4.5-linaro-r99464.patch \
       file://linaro/gcc-4.5-linaro-r99465.patch \
       file://linaro/gcc-4.5-linaro-r99466.patch \
       file://linaro/gcc-4.5-linaro-r99468.patch \
       file://linaro/gcc-4.5-linaro-r99473.patch \
       file://linaro/gcc-4.5-linaro-r99475.patch \
       file://linaro/gcc-4.5-linaro-r99478.patch \
       file://linaro/gcc-4.5-linaro-r99479.patch \
       file://linaro/gcc-4.5-linaro-r99480.patch \
       file://linaro/gcc-4.5-linaro-r99483.patch \
       file://linaro/gcc-4.5-linaro-r99488.patch \
       file://linaro/gcc-4.5-linaro-r99489.patch \
       file://linaro/gcc-4.5-linaro-r99491.patch \
       file://linaro/gcc-4.5-linaro-r99494.patch \
       file://linaro/gcc-4.5-linaro-r99495.patch \
       file://linaro/gcc-4.5-linaro-r99498.patch \
       file://linaro/gcc-4.5-linaro-r99502.patch \
       file://more-epilogues.patch \
       file://gcc-scalar-widening-pr45847.patch \
       file://gcc-arm-volatile-bitfield-fix.patch \
       \
       file://fedora/gcc43-c++-builtin-redecl.patch;striplevel=0 \
       file://fedora/gcc43-ia64-libunwind.patch;striplevel=0 \
       file://fedora/gcc43-java-nomulti.patch;striplevel=0 \
       file://fedora/gcc43-ppc32-retaddr.patch;striplevel=0 \
       file://fedora/gcc43-pr32139.patch;striplevel=0 \
       file://fedora/gcc43-pr33763.patch;striplevel=0 \
       file://fedora/gcc43-rh330771.patch;striplevel=0 \
       file://fedora/gcc43-rh341221.patch;striplevel=0 \
       file://fedora/gcc43-java-debug-iface-type.patch;striplevel=0 \
       file://fedora/gcc43-i386-libgomp.patch;striplevel=0 \
       file://fedora/gcc45-no-add-needed.patch;striplevel=0 \
       file://optional_libstdc.patch \
       file://64bithack.patch \
       file://GPLUSPLUS_INCLUDE_DIR_with_sysroot.patch \
       file://COLLECT_GCC_OPTIONS.patch \
       file://gcc-poison-dir-extend.patch \
       file://gcc-poison-parameters.patch \
       "

# Language Overrides
FORTRAN = ""
JAVA = ""

S = "${WORKDIR}/gcc-${BINV}"

#EXTRA_OECONF_BASE = "  --enable-cheaders=c_std \
#			--enable-libssp \
#			--disable-bootstrap \
#			--disable-libgomp \
#			--disable-libmudflap"
EXTRA_OECONF_BASE = "--enable-lto \
                     --enable-libssp \
                     --disable-bootstrap \
                     --disable-libgomp \
                     --disable-libmudflap \
                     --enable-cheaders=c_global "

EXTRA_OECONF_INITIAL = "--disable-libmudflap \
                        --disable-libgomp \
                        --disable-libssp \
                        --enable-decimal-float=no"

EXTRA_OECONF_INTERMEDIATE = "--disable-libmudflap \
                             --disable-libgomp \
                             --disable-libssp"

EXTRA_OECONF_append_libc-uclibc = " --disable-decimal-float "
EXTRA_OECONF_append_mips64 = " --with-arch-64=mips64 --with-tune-64=mips64"
EXTRA_OECONF_append_mips64el = " --with-arch-64=mips64 --with-tune-64=mips64"
