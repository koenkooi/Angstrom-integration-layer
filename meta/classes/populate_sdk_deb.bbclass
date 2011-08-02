do_populate_sdk[depends] += "dpkg-native:do_populate_sysroot apt-native:do_populate_sysroot bzip2-native:do_populate_sysroot"
do_populate_sdk[recrdeptask] += "do_package_write_deb"


populate_sdk_post_deb () {

	local target_rootfs=$1

	tar -cf -C ${STAGING_ETCDIR_NATIVE} -ps apt | tar -xf - -C ${target_rootfs}/etc
}

fakeroot populate_sdk_deb () {

	package_update_index_deb

	export INSTALL_TASK_DEB="populate_sdk"
	export INSTALL_PACKAGES_LINGUAS_DEB=""
	export INSTALL_PACKAGES_ATTEMPTONLY_DEB=""

	#install target
	echo "Installing TARGET packages"
	export INSTALL_ROOTFS_DEB="${SDK_OUTPUT}/${SDKTARGETSYSROOT}"
	export INSTALL_BASEARCH_DEB="${DPKG_ARCH}"
	export INSTALL_ARCHS_DEB="${PACKAGE_ARCHS}"
	export INSTALL_PACKAGES_NORMAL_DEB="${TOOLCHAIN_TARGET_TASK}"

	package_install_internal_deb
	populate_sdk_post_deb ${INSTALL_ROOTFS_DEB}

	populate_sdk_log_check populate_sdk

	#install host
	echo "Installing HOST packages"
	export INSTALL_ROOTFS_DEB="${SDK_OUTPUT}"
	export INSTALL_BASEARCH_DEB="${SDK_ARCH}"
	export INSTALL_PACKAGES_NORMAL_DEB="${TOOLCHAIN_HOST_TASK}"
	export INSTALL_ARCHS_DEB="${SDK_PACKAGE_ARCHS}"

	package_install_internal_deb
	populate_sdk_post_deb ${SDK_OUTPUT}/${SDKPATHNATIVE}

	#move remainings
	install -d ${SDK_OUTPUT}/${SDKPATHNATIVE}/var/dpkg
	mv ${SDK_OUTPUT}/var/dpkg/* ${SDK_OUTPUT}/${SDKPATHNATIVE}/var/dpkg
	rm -rf ${SDK_OUTPUT}/var

	populate_sdk_log_check populate_sdk
}

