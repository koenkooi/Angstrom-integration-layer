def get_links_from_url(url):
    "Return all the href links found on the web location"

    import urllib, sgmllib
    
    class LinksParser(sgmllib.SGMLParser):
        def parse(self, s):
            "Parse the given string 's'."
            self.feed(s)
            self.close()
    
        def __init__(self, verbose=0):
            "Initialise an object passing 'verbose' to the superclass."
            sgmllib.SGMLParser.__init__(self, verbose)
            self.hyperlinks = []
    
        def start_a(self, attributes):
            "Process a hyperlink and its 'attributes'."
            for name, value in attributes:
                if name == "href":
                    self.hyperlinks.append(value.strip('/'))
    
        def get_hyperlinks(self):
            "Return the list of hyperlinks."
            return self.hyperlinks

    sock = urllib.urlopen(url)
    webpage = sock.read()
    sock.close()

    linksparser = LinksParser()
    linksparser.parse(webpage)
    return linksparser.get_hyperlinks()

def find_latest_numeric_release(url):
    "Find the latest listed numeric release on the given url"
    max=0
    maxstr=""
    for link in get_links_from_url(url):
        try:
            release = float(link)
        except:
            release = 0
        if release > max:
            max = release
            maxstr = link
    return maxstr

def is_src_rpm(name):
    "Check if the link is pointing to a src.rpm file"
    if name[-8:] == ".src.rpm":
        return True
    else:
        return False

def package_name_from_srpm(srpm):
    "Strip out the package name from the src.rpm filename"
    strings = srpm.split('-')
    package_name = strings[0]
    for i in range(1, len (strings) - 1):
        str = strings[i]
        if not str[0].isdigit():
            package_name += '-' + str
    return package_name

def clean_package_list(package_list):
    "Removes multiple entries of packages and sorts the list"
    set = {}
    map(set.__setitem__, package_list, [])
    return set.keys()


def get_latest_released_meego_source_package_list():
    "Returns list of all the name os packages in the latest meego distro"

    
    f = open("/tmp/Meego-1.0", "r")
    package_names = []
    for line in f:
        package_names.append(line[:-1] + ":" + "main") # Also strip the '\n' at the end
     
    package_list=clean_package_list(package_names)
    return "1.0", package_list

def get_source_package_list_from_url(url, section):
    "Return a sectioned list of package names from a URL list"

    bb.note("Reading %s: %s" % (url, section))
    links = get_links_from_url(url)
    srpms = filter(is_src_rpm, links)
    names_list = map(package_name_from_srpm, srpms)

    new_pkgs = []
    for pkgs in names_list:
       new_pkgs.append(pkgs + ":" + section)

    return new_pkgs

def get_latest_released_fedora_source_package_list():
    "Returns list of all the name os packages in the latest fedora distro"
    latest = find_latest_numeric_release("http://download.fedora.redhat.com/pub/fedora/linux/releases/")

    package_names = get_source_package_list_from_url("http://download.fedora.redhat.com/pub/fedora/linux/releases/%s/Fedora/source/SRPMS/" % latest, "main")

#    package_names += get_source_package_list_from_url("http://download.fedora.redhat.com/pub/fedora/linux/releases/%s/Everything/source/SPRMS/" % latest, "everything")
    package_names += get_source_package_list_from_url("http://download.fedora.redhat.com/pub/fedora/linux/updates/%s/SRPMS/" % latest, "updates")

    package_list=clean_package_list(package_names)
        
    return latest, package_list

def get_latest_released_opensuse_source_package_list():
    "Returns list of all the name os packages in the latest opensuse distro"
    latest = find_latest_numeric_release("http://download.opensuse.org/source/distribution/")

    package_names = get_source_package_list_from_url("http://download.opensuse.org/source/distribution/%s/repo/oss/suse/src/" % latest, "main")
    package_names += get_source_package_list_from_url("http://download.opensuse.org/update/%s/rpm/src/" % latest, "updates")

    package_list=clean_package_list(package_names)
    return latest, package_list

def get_latest_released_mandriva_source_package_list():
    "Returns list of all the name os packages in the latest mandriva distro"
    latest = find_latest_numeric_release("http://distrib-coffee.ipsl.jussieu.fr/pub/linux/MandrivaLinux/official/")
    package_names = get_source_package_list_from_url("http://distrib-coffee.ipsl.jussieu.fr/pub/linux/MandrivaLinux/official/%s/SRPMS/main/release/" % latest, "main")
#    package_names += get_source_package_list_from_url("http://distrib-coffee.ipsl.jussieu.fr/pub/linux/MandrivaLinux/official/%s/SRPMS/contrib/release/" % latest, "contrib")
    package_names += get_source_package_list_from_url("http://distrib-coffee.ipsl.jussieu.fr/pub/linux/MandrivaLinux/official/%s/SRPMS/main/updates/" % latest, "updates")

    package_list=clean_package_list(package_names)
    return latest, package_list

def find_latest_debian_release(url):
    "Find the latest listed debian release on the given url"

    releases = []
    for link in get_links_from_url(url):
        if link[:6] == "Debian":
            if ';' not in link:
                releases.append(link)
    releases.sort()
    try:
        return releases.pop()[6:]
    except:
        return "_NotFound_"

def get_debian_style_source_package_list(url, section):
    "Return the list of package-names stored in the debian style Sources.gz file"
    import urllib
    sock = urllib.urlopen(url)
    import tempfile
    tmpfile = tempfile.NamedTemporaryFile(mode='wb', prefix='oecore.', suffix='.tmp', delete=False)
    tmpfilename=tmpfile.name
    tmpfile.write(sock.read())
    sock.close()
    tmpfile.close()
    import gzip
    bb.note("Reading %s: %s" % (url, section))

    f = gzip.open(tmpfilename)
    package_names = []
    for line in f:
        if line[:9] == "Package: ":
            package_names.append(line[9:-1] + ":" + section) # Also strip the '\n' at the end
    os.unlink(tmpfilename)

    return package_names

def get_latest_released_debian_source_package_list():
    "Returns list of all the name os packages in the latest debian distro"
    latest = find_latest_debian_release("http://ftp.debian.org/debian/dists/")
    url = "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz" 
    package_names = get_debian_style_source_package_list(url, "main")
#    url = "http://ftp.debian.org/debian/dists/stable/contrib/source/Sources.gz" 
#    package_names += get_debian_style_source_package_list(url, "contrib")
    url = "http://ftp.debian.org/debian/dists/stable-proposed-updates/main/source/Sources.gz" 
    package_names += get_debian_style_source_package_list(url, "updates")
    package_list=clean_package_list(package_names)
    return latest, package_list

def find_latest_ubuntu_release(url):
    "Find the latest listed ubuntu release on the given url"
    url += "?C=M;O=D" # Descending Sort by Last Modified
    for link in get_links_from_url(url):
        if link[-8:] == "-updates":
            return link[:-8]
    return "_NotFound_"

def get_latest_released_ubuntu_source_package_list():
    "Returns list of all the name os packages in the latest ubuntu distro"
    latest = find_latest_ubuntu_release("http://archive.ubuntu.com/ubuntu/dists/")
    url = "http://archive.ubuntu.com/ubuntu/dists/%s/main/source/Sources.gz" % latest
    package_names = get_debian_style_source_package_list(url, "main")
#    url = "http://archive.ubuntu.com/ubuntu/dists/%s/multiverse/source/Sources.gz" % latest
#    package_names += get_debian_style_source_package_list(url, "multiverse")
#    url = "http://archive.ubuntu.com/ubuntu/dists/%s/universe/source/Sources.gz" % latest
#    package_names += get_debian_style_source_package_list(url, "universe")
    url = "http://archive.ubuntu.com/ubuntu/dists/%s-updates/main/source/Sources.gz" % latest
    package_names += get_debian_style_source_package_list(url, "updates")
    package_list=clean_package_list(package_names)
    return latest, package_list

def create_distro_packages_list(distro_check_dir):
    pkglst_dir = os.path.join(distro_check_dir, "package_lists")
    if not os.path.isdir (pkglst_dir):
        os.makedirs(pkglst_dir)
    # first clear old stuff
    for file in os.listdir(pkglst_dir):
        os.unlink(os.path.join(pkglst_dir, file))
 
    per_distro_functions = [
                            ["Debian", get_latest_released_debian_source_package_list],
                            ["Ubuntu", get_latest_released_ubuntu_source_package_list],
                            ["Fedora", get_latest_released_fedora_source_package_list],
                            ["OpenSuSE", get_latest_released_opensuse_source_package_list],
                            ["Mandriva", get_latest_released_mandriva_source_package_list],
                            ["Meego", get_latest_released_meego_source_package_list]
                           ]
 
    from datetime import datetime
    begin = datetime.now()
    for distro in per_distro_functions:
        name = distro[0]
        release, package_list = distro[1]()
        bb.note("Distro: %s, Latest Release: %s, # src packages: %d" % (name, release, len(package_list)))
        package_list_file = os.path.join(pkglst_dir, name + "-" + release)
        f = open(package_list_file, "w+b")
        for pkg in package_list:
            f.write(pkg + "\n")
        f.close()
    end = datetime.now()
    delta = end - begin
    bb.note("package_list generatiosn took this much time: %d seconds" % delta.seconds)

def update_distro_data(distro_check_dir, datetime):
    """
        If distro packages list data is old then rebuild it.
        The operations has to be protected by a lock so that
        only one thread performes it at a time.
    """
    if not os.path.isdir (distro_check_dir):
        try:
            bb.note ("Making new directory: %s" % distro_check_dir)
            os.makedirs (distro_check_dir)
        except OSError:
            raise Exception('Unable to create directory %s' % (distro_check_dir))


    datetime_file = os.path.join(distro_check_dir, "build_datetime")
    saved_datetime = "_invalid_"
    import fcntl
    try:
        if not os.path.exists(datetime_file):
            open(datetime_file, 'w+b').close() # touch the file so that the next open won't fail

        f = open(datetime_file, "r+b")
        fcntl.lockf(f, fcntl.LOCK_EX)
        saved_datetime = f.read()
        if saved_datetime[0:8] != datetime[0:8]:
            bb.note("The build datetime did not match: saved:%s current:%s" % (saved_datetime, datetime))
            bb.note("Regenerating distro package lists")
            create_distro_packages_list(distro_check_dir)
            f.seek(0)
            f.write(datetime)

    except OSError:
        raise Exception('Unable to read/write this file: %s' % (datetime_file))
    finally:
        fcntl.lockf(f, fcntl.LOCK_UN)
        f.close()
 
def compare_in_distro_packages_list(distro_check_dir, d):
    if not os.path.isdir(distro_check_dir):
        raise Exception("compare_in_distro_packages_list: invalid distro_check_dir passed")
        
    localdata = bb.data.createCopy(d)
    pkglst_dir = os.path.join(distro_check_dir, "package_lists")
    matching_distros = []
    pn = bb.data.getVar('PN', d, True)
    recipe_name = bb.data.getVar('PN', d, True)
    bb.note("Checking: %s" % pn)

    trim_dict = dict({"-native":"-native", "-cross":"-cross", "-initial":"-initial"})

    if pn.find("-native") != -1:
        pnstripped = pn.split("-native")
        bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
        bb.data.update_data(localdata)
        recipe_name = pnstripped[0]

    if pn.find("-cross") != -1:
        pnstripped = pn.split("-cross")
        bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
        bb.data.update_data(localdata)
        recipe_name = pnstripped[0]

    if pn.find("-initial") != -1:
        pnstripped = pn.split("-initial")
        bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
        bb.data.update_data(localdata)
        recipe_name = pnstripped[0]

    bb.note("Recipe: %s" % recipe_name)
    tmp = bb.data.getVar('DISTRO_PN_ALIAS', localdata, True)

    distro_exceptions = dict({"OE-Core":'OE-Core', "OpenedHand":'OpenedHand', "Intel":'Intel', "Upstream":'Upstream', "WindRiver":'Windriver', "OSPDT":'OSPDT Approved', "Poky":'poky'})

    if tmp:
        list = tmp.split(' ')
        for str in list:
            if str and str.find("=") == -1 and distro_exceptions[str]:
                matching_distros.append(str)

    distro_pn_aliases = {}
    if tmp:
        list = tmp.split(' ')
        for str in list:
            if str.find("=") != -1:
                (dist, pn_alias) = str.split('=')
                distro_pn_aliases[dist.strip().lower()] = pn_alias.strip()
 
    for file in os.listdir(pkglst_dir):
        (distro, distro_release) = file.split("-")
        f = open(os.path.join(pkglst_dir, file), "rb")
        for line in f:
            (pkg, section) = line.split(":")
            if distro.lower() in distro_pn_aliases:
                pn = distro_pn_aliases[distro.lower()]
            else:
                pn = recipe_name
            if pn == pkg:
                matching_distros.append(distro + "-" + section[:-1]) # strip the \n at the end
                f.close()
                break
        f.close()

    
    if tmp != None:
	list = tmp.split(' ')
	for item in list:
            matching_distros.append(item)
    bb.note("Matching: %s" % matching_distros)
    return matching_distros

def save_distro_check_result(result, datetime, d):
    pn = bb.data.getVar('PN', d, True)
    logdir = bb.data.getVar('LOG_DIR', d, True)
    if not logdir:
        bb.error("LOG_DIR variable is not defined, can't write the distro_check results")
        return
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    result_file = os.path.join(logdir, "distrocheck.%s.csv" % datetime)
    line = pn
    for i in result:
        line = line + "," + i
    if not os.path.exists(result_file):
        sresult_file = os.path.join(logdir, "distrocheck.csv")
	if os.path.exists(sresult_file):
	    os.remove(sresult_file)
	os.system("touch %s" % result_file)
	os.symlink(result_file, sresult_file)
    f = open(result_file, "a")
    import fcntl
    fcntl.lockf(f, fcntl.LOCK_EX)
    f.seek(0, os.SEEK_END) # seek to the end of file
    f.write(line + "\n")
    fcntl.lockf(f, fcntl.LOCK_UN)
    f.close()
