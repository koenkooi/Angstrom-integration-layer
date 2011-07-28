require conf/distro/include/distro_tracking_fields.inc

addhandler distro_eventhandler
python distro_eventhandler() {

    if bb.event.getName(e) == "BuildStarted":
	"""initialize log files."""
	logpath = bb.data.getVar('LOG_DIR', e.data, 1)
	bb.utils.mkdirhier(logpath)
	logfile = os.path.join(logpath, "distrodata.%s.csv" % bb.data.getVar('DATETIME', e.data, 1))
	if not os.path.exists(logfile):
		slogfile = os.path.join(logpath, "distrodata.csv")
		if os.path.exists(slogfile):
			os.remove(slogfile)
		os.system("touch %s" % logfile)
		os.symlink(logfile, slogfile)
		bb.data.setVar('LOG_FILE', logfile, e.data)

	lf = bb.utils.lockfile(logfile + ".lock")
	f = open(logfile, "a")
	f.write("Package,Description,Owner,License,ChkSum,Status,VerMatch,Version,Upsteam,Non-Update,Reason,Recipe Status\n")
        f.close()
        bb.utils.unlockfile(lf)

    return
}

addtask distrodata_np
do_distrodata_np[nostamp] = "1"
python do_distrodata_np() {
	localdata = bb.data.createCopy(d)
        pn = bb.data.getVar("PN", d, True)
        bb.note("Package Name: %s" % pn)

        import oe.distro_check as dist_check
        tmpdir = bb.data.getVar('TMPDIR', d, 1)
        distro_check_dir = os.path.join(tmpdir, "distro_check")
        datetime = bb.data.getVar('DATETIME', localdata, 1)
        dist_check.update_distro_data(distro_check_dir, datetime)

	if pn.find("-native") != -1:
	    pnstripped = pn.split("-native")
	    bb.note("Native Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	if pn.find("-cross") != -1:
	    pnstripped = pn.split("-cross")
	    bb.note("cross Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	if pn.find("-initial") != -1:
	    pnstripped = pn.split("-initial")
	    bb.note("initial Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	"""generate package information from .bb file"""
	pname = bb.data.getVar('PN', localdata, True)
	pcurver = bb.data.getVar('PV', localdata, True)
	pdesc = bb.data.getVar('DESCRIPTION', localdata, True)
        if pdesc is not None:
                pdesc = pdesc.replace(',','')
                pdesc = pdesc.replace('\n','')

	pgrp = bb.data.getVar('SECTION', localdata, True)
	plicense = bb.data.getVar('LICENSE', localdata, True).replace(',','_')
	if bb.data.getVar('LIC_FILES_CHKSUM', localdata, True):
		pchksum="1"
	else:
		pchksum="0"

	if bb.data.getVar('RECIPE_STATUS', localdata, True):
		hasrstatus="1"
	else:
		hasrstatus="0"

	rstatus = bb.data.getVar('RECIPE_STATUS', localdata, True)
        if rstatus is not None:
                rstatus = rstatus.replace(',','')
		
	pupver = bb.data.getVar('RECIPE_LATEST_VERSION', localdata, True)
	if pcurver == pupver:
		vermatch="1"
	else:
		vermatch="0"
	noupdate_reason = bb.data.getVar('RECIPE_NO_UPDATE_REASON', localdata, True)
	if noupdate_reason is None:
		noupdate="0"
	else:
		noupdate="1"
                noupdate_reason = noupdate_reason.replace(',','')

	ris = bb.data.getVar('RECIPE_INTEL_SECTION', localdata, True)
	maintainer = bb.data.getVar('RECIPE_MAINTAINER', localdata, True)
	rttr = bb.data.getVar('RECIPE_TIME_BETWEEN_LAST_TWO_RELEASES', localdata, True)
	rlrd = bb.data.getVar('RECIPE_LATEST_RELEASE_DATE', localdata, True)
	dc = bb.data.getVar('DEPENDENCY_CHECK', localdata, True)
	rc = bb.data.getVar('RECIPE_COMMENTS', localdata, True)
        result = dist_check.compare_in_distro_packages_list(distro_check_dir, localdata)

	bb.note("DISTRO: %s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s\n" % \
		  (pname, pdesc, maintainer, plicense, pchksum, hasrstatus, vermatch, pcurver, pupver, noupdate, noupdate_reason, rstatus))
        line = pn
        for i in result:
            line = line + "," + i
        bb.note("%s\n" % line)
}

addtask distrodata
do_distrodata[nostamp] = "1"
python do_distrodata() {
	logpath = bb.data.getVar('LOG_DIR', d, 1)
	bb.utils.mkdirhier(logpath)
	logfile = os.path.join(logpath, "distrodata.csv")

        import oe.distro_check as dist_check
	localdata = bb.data.createCopy(d)
        tmpdir = bb.data.getVar('TMPDIR', d, 1)
        distro_check_dir = os.path.join(tmpdir, "distro_check")
        datetime = bb.data.getVar('DATETIME', localdata, 1)
        dist_check.update_distro_data(distro_check_dir, datetime)

        pn = bb.data.getVar("PN", d, True)
        bb.note("Package Name: %s" % pn)

	if pn.find("-native") != -1:
	    pnstripped = pn.split("-native")
	    bb.note("Native Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	if pn.find("-cross") != -1:
	    pnstripped = pn.split("-cross")
	    bb.note("cross Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	if pn.find("-initial") != -1:
	    pnstripped = pn.split("-initial")
	    bb.note("initial Split: %s" % pnstripped)
	    bb.data.setVar('OVERRIDES', "pn-" + pnstripped[0] + ":" + bb.data.getVar('OVERRIDES', d, True), localdata)
	    bb.data.update_data(localdata)

	"""generate package information from .bb file"""
	pname = bb.data.getVar('PN', localdata, True)
	pcurver = bb.data.getVar('PV', localdata, True)
	pdesc = bb.data.getVar('DESCRIPTION', localdata, True)
        if pdesc is not None:
                pdesc = pdesc.replace(',','')
                pdesc = pdesc.replace('\n','')

	pgrp = bb.data.getVar('SECTION', localdata, True)
	plicense = bb.data.getVar('LICENSE', localdata, True).replace(',','_')
	if bb.data.getVar('LIC_FILES_CHKSUM', localdata, True):
		pchksum="1"
	else:
		pchksum="0"

	if bb.data.getVar('RECIPE_STATUS', localdata, True):
		hasrstatus="1"
	else:
		hasrstatus="0"

	rstatus = bb.data.getVar('RECIPE_STATUS', localdata, True)
        if rstatus is not None:
                rstatus = rstatus.replace(',','')
		
	pupver = bb.data.getVar('RECIPE_LATEST_VERSION', localdata, True)
	if pcurver == pupver:
		vermatch="1"
	else:
		vermatch="0"

	noupdate_reason = bb.data.getVar('RECIPE_NO_UPDATE_REASON', localdata, True)
	if noupdate_reason is None:
		noupdate="0"
	else:
		noupdate="1"
                noupdate_reason = noupdate_reason.replace(',','')

	ris = bb.data.getVar('RECIPE_INTEL_SECTION', localdata, True)
	maintainer = bb.data.getVar('RECIPE_MAINTAINER', localdata, True)
	rttr = bb.data.getVar('RECIPE_TIME_BETWEEN_LAST_TWO_RELEASES', localdata, True)
	rlrd = bb.data.getVar('RECIPE_LATEST_RELEASE_DATE', localdata, True)
	dc = bb.data.getVar('DEPENDENCY_CHECK', localdata, True)
	rc = bb.data.getVar('RECIPE_COMMENTS', localdata, True)
        # do the comparison
        result = dist_check.compare_in_distro_packages_list(distro_check_dir, localdata)

	lf = bb.utils.lockfile(logfile + ".lock")
	f = open(logfile, "a")
	f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," % \
		  (pname, pdesc, maintainer, plicense, pchksum, hasrstatus, vermatch, pcurver, pupver, noupdate, noupdate_reason, rstatus))
        line = ""
        for i in result:
            line = line + "," + i
        f.write(line + "\n")
        f.close()
        bb.utils.unlockfile(lf)
}

addtask distrodataall after do_distrodata
do_distrodataall[recrdeptask] = "do_distrodata"
do_distrodataall[nostamp] = "1"
do_distrodataall() {
	:
}

addhandler checkpkg_eventhandler
python checkpkg_eventhandler() {
    if bb.event.getName(e) == "BuildStarted":
	"""initialize log files."""
	logpath = bb.data.getVar('LOG_DIR', e.data, 1)
	bb.utils.mkdirhier(logpath)
	logfile = os.path.join(logpath, "checkpkg.%s.csv" % bb.data.getVar('DATETIME', e.data, 1))
	if not os.path.exists(logfile):
		slogfile = os.path.join(logpath, "checkpkg.csv")
		if os.path.exists(slogfile):
			os.remove(slogfile)
		os.system("touch %s" % logfile)
		os.symlink(logfile, slogfile)
		bb.data.setVar('LOG_FILE', logfile, e.data)

	lf = bb.utils.lockfile(logfile + ".lock")
	f = open(logfile, "a")
	f.write("Package\tOwner\tURI Type\tVersion\tTracking\tUpstream\tTMatch\tRMatch\n")
        f.close()
        bb.utils.unlockfile(lf)
	"""initialize log files for package report system"""
	logfile2 = os.path.join(logpath, "get_pkg_info.%s.log" % bb.data.getVar('DATETIME', e.data, 1))
	if not os.path.exists(logfile2):
		slogfile2 = os.path.join(logpath, "get_pkg_info.log")
		if os.path.exists(slogfile2):
			os.remove(slogfile2)
		os.system("touch %s" % logfile2)
		os.symlink(logfile2, slogfile2)
    return
}

addtask checkpkg
do_checkpkg[nostamp] = "1"
python do_checkpkg() {
	import sys
	import re
	import tempfile

	"""
	sanity check to ensure same name and type. Match as many patterns as possible
	such as:
		gnome-common-2.20.0.tar.gz (most common format)
		gtk+-2.90.1.tar.gz
		xf86-intput-synaptics-12.6.9.tar.gz
		dri2proto-2.3.tar.gz
		blktool_4.orig.tar.gz
		libid3tag-0.15.1b.tar.gz
		unzip552.tar.gz
		icu4c-3_6-src.tgz
		genext2fs_1.3.orig.tar.gz
		gst-fluendo-mp3
	"""
	prefix1 = "[a-zA-Z][a-zA-Z0-9]*([\-_][a-zA-Z]\w+)*[\-_]"	# match most patterns which uses "-" as separator to version digits
	prefix2 = "[a-zA-Z]+"			# a loose pattern such as for unzip552.tar.gz
	prefix3 = "[0-9a-zA-Z]+"			# a loose pattern such as for 80325-quicky-0.4.tar.gz
	prefix = "(%s|%s|%s)" % (prefix1, prefix2, prefix3)
	suffix = "(tar\.gz|tgz|tar\.bz2|zip|xz|rpm)"
	suffixtuple = ("tar.gz", "tgz", "zip", "tar.bz2", "tar.xz", "src.rpm")

	sinterstr = "(?P<name>%s?)(?P<ver>.*)" % prefix
	sdirstr = "(?P<name>%s)(?P<ver>.*)\.(?P<type>%s$)" % (prefix, suffix)

	def parse_inter(s):
		m = re.search(sinterstr, s)
		if not m:
			return None
		else:
			return (m.group('name'), m.group('ver'), "")

	def parse_dir(s):
		m = re.search(sdirstr, s)
		if not m:
			return None
		else:
			return (m.group('name'), m.group('ver'), m.group('type'))

	"""
	Check whether 'new' is newer than 'old' version. We use existing vercmp() for the
	purpose. PE is cleared in comparison as it's not for build, and PV is cleared too
	for simplicity as it's somehow difficult to get from various upstream format
	"""
	def __vercmp(old, new):
		(on, ov, ot) = old
		(en, ev, et) = new
		if on != en or (et and et not in suffixtuple):
			return 0
		ov = re.search("[\d|\.]+[^a-zA-Z]+", ov).group()
		ev = re.search("[\d|\.]+[^a-zA-Z]+", ev).group()
		return bb.utils.vercmp(("0", ov, ""), ("0", ev, ""))

	"""
	wrapper for fetch upstream directory info
		'url'	- upstream link customized by regular expression
		'd'	- database
		'tmpf'	- tmpfile for fetcher output
	We don't want to exit whole build due to one recipe error. So handle all exceptions 
	gracefully w/o leaking to outer. 
	"""
	def internal_fetch_wget(url, d, tmpf):
		status = "ErrFetchUnknown"
		"""
		Clear internal url cache as it's a temporary check. Not doing so will have 
		bitbake check url multiple times when looping through a single url
		"""
		fn = bb.data.getVar('FILE', d, 1)
		bb.fetch2.urldata_cache[fn] = {}

		"""
		To avoid impacting bitbake build engine, this trick is required for reusing bitbake
		interfaces. bb.fetch.go() is not appliable as it checks downloaded content in ${DL_DIR}
		while we don't want to pollute that place. So bb.fetch2.checkstatus() is borrowed here
		which is designed for check purpose but we override check command for our own purpose
		"""
		ld = bb.data.createCopy(d)
		bb.data.setVar('CHECKCOMMAND_wget', "/usr/bin/env wget -t 1 --passive-ftp -O %s --user-agent=\"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.12) Gecko/20101027 Ubuntu/9.10 (karmic) Firefox/3.6.12\" '${URI}'" \
					% tmpf.name, d)
		bb.data.update_data(ld)

		try:
			fetcher = bb.fetch2.Fetch([url], ld)
			fetcher.checkstatus()
			status = "SUCC"
		except bb.fetch2.BBFetchException, e:
			status = "ErrFetch"

		return status

	"""
	Check on middle version directory such as "2.4/" in "http://xxx/2.4/pkg-2.4.1.tar.gz", 
		'url'	- upstream link customized by regular expression
		'd'	- database
		'curver' - current version
	Return new version if success, or else error in "Errxxxx" style
	"""
	def check_new_dir(url, curver, d):
		pn = bb.data.getVar('PN', d, 1)
		f = tempfile.NamedTemporaryFile(delete=False, prefix="%s-1-" % pn)
		status = internal_fetch_wget(url, d, f)
		fhtml = f.read()
		if status == "SUCC" and len(fhtml):
			newver = parse_inter(curver)

			"""
			match "*4.1/">*4.1/ where '*' matches chars
			N.B. add package name, only match for digits
			"""
			m = re.search("^%s" % prefix, curver)
			if m:
				s = "%s[^\d\"]*?(\d+[\.\-_])+\d+/?" % m.group()
			else:
				s = "(\d+[\.\-_])+\d+/?"
				
			searchstr = "[hH][rR][eE][fF]=\"%s\">" % s
			reg = re.compile(searchstr)

			valid = 0
			for line in fhtml.split("\n"):
				if line.find(curver) >= 0:
					valid = 1
				m = reg.search(line)
				if m:
					ver = m.group().split("\"")[1]
					ver = ver.strip("/")
					ver = parse_inter(ver)
					if ver and __vercmp(newver, ver) < 0:
						newver = ver

			"""Expect a match for curver in directory list, or else it indicates unknown format"""
			if not valid:
				status = "ErrParseInterDir"
			else:
				"""rejoin the path name"""
				status = newver[0] + newver[1]
		elif not len(fhtml):
			status = "ErrHostNoDir"

		f.close()
		if status != "ErrHostNoDir" and re.match("Err", status):
			logpath = bb.data.getVar('LOG_DIR', d, 1)
			os.system("cp %s %s/" % (f.name, logpath))
		os.unlink(f.name)
		return status

	"""
	Check on the last directory to search '2.4.1' in "http://xxx/2.4/pkg-2.4.1.tar.gz", 
		'url'	- upstream link customized by regular expression
		'd'	- database
		'curname' - current package name
	Return new version if success, or else error in "Errxxxx" style
	"""
	def check_new_version(url, curname, d):
		"""possible to have no version in pkg name, such as spectrum-fw"""
		if not re.search("\d+", curname):
			return pcurver
		pn = bb.data.getVar('PN', d, 1)
		f = tempfile.NamedTemporaryFile(delete=False, prefix="%s-2-" % pn)
		status = internal_fetch_wget(url, d, f)
		fhtml = f.read()

		if status == "SUCC" and len(fhtml):
			newver = parse_dir(curname)

			"""match "{PN}-5.21.1.tar.gz">{PN}-5.21.1.tar.gz """
			pn1 = re.search("^%s" % prefix, curname).group()
			
			s = "[^\"]*%s[^\d\"]*?(\d+[\.\-_])+[^\"]*" % pn1
			searchstr = "[hH][rR][eE][fF]=\"%s\".*[>\"]" % s
			reg = re.compile(searchstr)
	
			valid = 0
			for line in fhtml.split("\n"):
				m = reg.search(line)
				if m:
					valid = 1
					ver = m.group().split("\"")[1].split("/")[-1]
					if ver == "download":
						ver = m.group().split("\"")[1].split("/")[-2]
					ver = parse_dir(ver)
					if ver and __vercmp(newver, ver) < 0:
						newver = ver
	
			"""Expect a match for curver in directory list, or else it indicates unknown format"""
			if not valid:
				status = "ErrParseDir"
			else:
				"""newver still contains a full package name string"""
				status = re.search("(\d+[\.\-_])*(\d+[0-9a-zA-Z]*)", newver[1]).group()
				if "_" in status:
					status = re.sub("_",".",status)
				elif "-" in status:
					status = re.sub("-",".",status)
		elif not len(fhtml):
			status = "ErrHostNoDir"

		f.close()
		"""if host hasn't directory information, no need to save tmp file"""
		if status != "ErrHostNoDir" and re.match("Err", status):
			logpath = bb.data.getVar('LOG_DIR', d, 1)
			os.system("cp %s %s/" % (f.name, logpath))
		os.unlink(f.name)
		return status

	"""first check whether a uri is provided"""
	src_uri = bb.data.getVar('SRC_URI', d, 1)
	if not src_uri:
		return

	"""initialize log files."""
	logpath = bb.data.getVar('LOG_DIR', d, 1)
	bb.utils.mkdirhier(logpath)
	logfile = os.path.join(logpath, "checkpkg.csv")
	"""initialize log files for package report system"""
	logfile2 = os.path.join(logpath, "get_pkg_info.log")

	"""generate package information from .bb file"""
	pname = bb.data.getVar('PN', d, 1)
	pdesc = bb.data.getVar('DESCRIPTION', d, 1)
	pgrp = bb.data.getVar('SECTION', d, 1)
	pversion = bb.data.getVar('PV', d, 1)
	plicense = bb.data.getVar('LICENSE',d,1)
	psection = bb.data.getVar('SECTION',d,1)
	phome = bb.data.getVar('HOMEPAGE', d, 1)
	prelease = bb.data.getVar('PR',d,1)
	ppriority = bb.data.getVar('PRIORITY',d,1)
	pdepends = bb.data.getVar('DEPENDS',d,1)
	pbugtracker = bb.data.getVar('BUGTRACKER',d,1)
	ppe = bb.data.getVar('PE',d,1)
	psrcuri = bb.data.getVar('SRC_URI',d,1)

	found = 0
	for uri in src_uri.split():
		m = re.compile('(?P<type>[^:]*)').match(uri)
		if not m:
			raise MalformedUrl(uri)
		elif m.group('type') in ('http', 'https', 'ftp', 'cvs', 'svn', 'git'):
			found = 1
			pproto = m.group('type')
			break
	if not found:
		pproto = "file"
	pupver = "N/A"
	pstatus = "ErrUnknown"

	(type, host, path, user, pswd, parm) = bb.decodeurl(uri)
	if type in ['http', 'https', 'ftp']:
		pcurver = bb.data.getVar('PV', d, 1)
	else:
		pcurver = bb.data.getVar("SRCREV", d, 1)

	if type in ['http', 'https', 'ftp']:
		newver = pcurver
		altpath = path
		dirver = "-"
		curname = "-"
	
		"""
		match version number amid the path, such as "5.7" in:
			http://download.gnome.org/sources/${PN}/5.7/${PN}-${PV}.tar.gz	
		N.B. how about sth. like "../5.7/5.8/..."? Not find such example so far :-P
		"""
		m = re.search(r"[^/]*(\d+\.)+\d+([\-_]r\d+)*/", path)
		if m:
			altpath = path.split(m.group())[0]
			dirver = m.group().strip("/")
	
			"""use new path and remove param. for wget only param is md5sum"""
			alturi = bb.encodeurl([type, host, altpath, user, pswd, {}])
	
			newver = check_new_dir(alturi, dirver, d)
			altpath = path
			if not re.match("Err", newver) and dirver != newver:
				altpath = altpath.replace(dirver, newver, 1)
				
		"""Now try to acquire all remote files in current directory"""
		if not re.match("Err", newver):
			curname = altpath.split("/")[-1]
	
			"""get remote name by skipping pacakge name"""
			m = re.search(r"/.*/", altpath)
			if not m:
				altpath = "/"
			else:
				altpath = m.group()
	
			alturi = bb.encodeurl([type, host, altpath, user, pswd, {}])
			newver = check_new_version(alturi, curname, d)
			while(newver == "ErrHostNoDir"):
				if alturi == "/download":
					break
				else:
					alturi = "/".join(alturi.split("/")[0:-2]) + "/download"
					newver = check_new_version(alturi, curname, d)
			if not re.match("Err", newver):
				pupver = newver
				if pupver != pcurver:
					pstatus = "UPDATE"
				else:
					pstatus = "MATCH"
	
		if re.match("Err", newver):
			pstatus = newver + ":" + altpath + ":" + dirver + ":" + curname
	elif type == 'git':
		if user:
			gituser = user + '@'
		else:
			gituser = ""

		if 'protocol' in parm:
			gitproto = parm['protocol']
		else:
			gitproto = "rsync"
		gitcmd = "git ls-remote %s://%s%s%s *tag* 2>&1" % (gitproto, gituser, host, path)
		gitcmd2 = "git ls-remote %s://%s%s%s HEAD 2>&1" % (gitproto, gituser, host, path)
		tmp = os.popen(gitcmd).read()
		tmp2 = os.popen(gitcmd2).read()
		#This is for those repo have tag like: refs/tags/1.2.2
		if tmp:
			tmpline = tmp.split("\n")
			verflag = 0
			for line in tmpline:
				if len(line)==0:
					break;
				puptag = line.split("/")[-1]
				puptag = re.search("[0-9][0-9|\.|_]+[0-9]", puptag)
				if puptag == None:
					continue;
				puptag = puptag.group()
				puptag = re.sub("_",".",puptag)
				plocaltag = pversion.split("+")[0]
				if "git" in plocaltag:
					plocaltag = plocaltag.split("-")[0]
				result = bb.utils.vercmp(("0", puptag, ""), ("0", plocaltag, ""))
				if result > 0:
					verflag = 1
					pstatus = "UPADTE"
					pupver = puptag
				elif verflag == 0 :
					pupver = plocaltag
					pstatus = "MATCH"
		#This is for those no tag repo
		elif tmp2:
			pupver = tmp2.split("\t")[0]
			if pupver in pversion:
				pstatus = "MATCH"
			else:
				pstatus = "UPDATE"
		else:
			pstatus = "ErrGitAccess"
	elif type == 'svn':
		options = []
		if user:
			options.append("--username %s" % user)
		if pswd:
			options.append("--password %s" % pswd)
		svnproto = 'svn'
		if 'proto' in parm:
			svnproto = parm['proto']
		if 'rev' in parm:
			pcurver = parm['rev']

		svncmd = "svn info %s %s://%s%s/%s/ 2>&1" % (" ".join(options), svnproto, host, path, parm["module"])
		print svncmd
		svninfo = os.popen(svncmd).read()
		for line in svninfo.split("\n"):
			if re.search("^Last Changed Rev:", line):
				pupver = line.split(" ")[-1]
				if pupver in pversion:
					pstatus = "MATCH"
				else:
					pstatus = "UPDATE"

		if re.match("Err", pstatus):
			pstatus = "ErrSvnAccess"
	elif type == 'cvs':
		pupver = "HEAD"
		pstatus = "UPDATE"
	elif type == 'file':
		"""local file is always up-to-date"""
		pupver = pcurver
		pstatus = "MATCH"
	else:
		pstatus = "ErrUnsupportedProto"

	if re.match("Err", pstatus):
		pstatus += ":%s%s" % (host, path)

	"""Read from manual distro tracking fields as alternative"""
	pmver = bb.data.getVar("RECIPE_LATEST_VERSION", d, 1)
	if not pmver:
		pmver = "N/A"
		pmstatus = "ErrNoRecipeData"
	else:
		if pmver == pcurver:
			pmstatus = "MATCH"
		else:
			pmstatus = "UPDATE"
	
	maintainer = bb.data.getVar('RECIPE_MAINTAINER', d, True)
	lf = bb.utils.lockfile(logfile + ".lock")
	f = open(logfile, "a")
	f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % \
		  (pname, maintainer, pproto, pcurver, pmver, pupver, pmstatus, pstatus))
	f.close()
	bb.utils.unlockfile(lf)

	"""write into get_pkg_info log file to supply data for package report system"""
	lf2 = bb.utils.lockfile(logfile2 + ".lock")
	f2 = open(logfile2, "a")
	f2.write("%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n" % \
		  (pname,pversion,pupver,plicense,psection, phome,prelease, ppriority,pdepends,pbugtracker,ppe,pdesc,pstatus,pmver,psrcuri))
	f2.close()
	bb.utils.unlockfile(lf2)
}

addtask checkpkgall after do_checkpkg
do_checkpkgall[recrdeptask] = "do_checkpkg"
do_checkpkgall[nostamp] = "1"
do_checkpkgall() {
	:
}

#addhandler check_eventhandler
python check_eventhandler() {
    if bb.event.getName(e) == "BuildStarted":
        import oe.distro_check as dc
        tmpdir = bb.data.getVar('TMPDIR', e.data, 1)
        distro_check_dir = os.path.join(tmpdir, "distro_check")
        datetime = bb.data.getVar('DATETIME', e.data, 1)
        """initialize log files."""
        logpath = bb.data.getVar('LOG_DIR', e.data, 1)
        bb.utils.mkdirhier(logpath)
        logfile = os.path.join(logpath, "distrocheck.%s.csv" % bb.data.getVar('DATETIME', e.data, 1))
        if not os.path.exists(logfile):
                slogfile = os.path.join(logpath, "distrocheck.csv")
                if os.path.exists(slogfile):
                        os.remove(slogfile)
                os.system("touch %s" % logfile)
                os.symlink(logfile, slogfile)
                bb.data.setVar('LOG_FILE', logfile, e.data)

    return
}

addtask distro_check
do_distro_check[nostamp] = "1"
python do_distro_check() {
    """checks if the package is present in other public Linux distros"""
    import oe.distro_check as dc
    localdata = bb.data.createCopy(d)
    bb.data.update_data(localdata)
    tmpdir = bb.data.getVar('TMPDIR', d, 1)
    distro_check_dir = os.path.join(tmpdir, "distro_check")
    datetime = bb.data.getVar('DATETIME', localdata, 1)
    dc.update_distro_data(distro_check_dir, datetime)

    # do the comparison
    result = dc.compare_in_distro_packages_list(distro_check_dir, d)

    # save the results
    dc.save_distro_check_result(result, datetime, d)
}

addtask distro_checkall after do_distro_check
do_distro_checkall[recrdeptask] = "do_distro_check"
do_distro_checkall[nostamp] = "1"
do_distro_checkall() {
	:
}
