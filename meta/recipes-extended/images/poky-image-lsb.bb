IMAGE_FEATURES += "apps-console-core ssh-server-openssh"

IMAGE_INSTALL = "\
    ${POKY_BASE_INSTALL} \
    task-poky-basic \
    task-poky-lsb \
    "

inherit poky-image
