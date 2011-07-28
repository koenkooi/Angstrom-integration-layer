DESCRIPTION = "guilt is quilt like tool for git"
LICENSE = "GPLv2"

LIC_FILES_CHKSUM = "file://COPYING;md5=b6f3400dc1a01cebafe8a52b3f344135"

PR = r0
PV = "0.33"

inherit native

SRC_URI = "${KERNELORG_MIRROR}/linux/kernel/people/jsipek/guilt/guilt-${PV}.tar.gz\
           file://guilt-push.patch \
	   file://guilt-pop.patch \
	   file://guilt.patch \
	   file://guilt-init.patch \
	   file://guilt-import-commit.patch \
	   file://uninstall_force.patch \
	   file://guilt-push-no-series.patch \
	   file://make_git_commands_conditional.patch \
	   file://improve_auto_header_gen.patch \
	   file://guilt-set-git_exec_path.patch \
	   file://guilt-bash.patch \
	   file://optional_head_check.patch"

# we don't compile, we just install
do_compile() {
	:
}

do_install() {
	oe_runmake PREFIX=${D}/${base_prefix}/usr install
}
