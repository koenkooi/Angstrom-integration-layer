DESCRIPTION = "Task packages for the Angstrom distribution"
PR = "r32"

inherit task

RDEPENDS_${PN} = "\
    gnumeric \
    abiword \
    imposter \
    evince \
    gqview"

