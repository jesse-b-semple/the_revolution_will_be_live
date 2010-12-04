#!/usr/bin/python
#  the_revolution_will_be_live v1
#  by Jesse B. Semple 
#  This here will copy them cables from that foreigner to them
#  beetnik blogs that kids love so much these days. I'm over 
#  80 years young so don't be asking me to code proper.
#
#  latest code, bugs'n'patches over at:
#  http://github.com/jesse-b-semple/the_revolution_will_be_live
#  or post it anonymously (perhaps using tor) at:
#  http://pastbin  and add a tag "cablegate"
#  I will search for new posts with that tag regularly
#
VERSION=1

import BeautifulSoup
import blogapi as pyblog #based on pyblog but includes http proxy support

import re
import urllib
import urlparse
import os, os.path
import getopt, sys
from getpass import getpass

cablegateurl = "http://213.251.145.96/cablegate.html"
cablegate_prefix = '://'.join(urlparse.urlsplit(cablegateurl)[0:2])
user         = False
password     = False
blogrpcurl   = False
blogid       = 0
bloggetlist  = False
blogtype     = "wordpress"
proxyurl	 = None
proxy        = None
nodamnpoetry = False

VERBOSE      = False
idxdir 		 = "reldate" # need to match site url directory for index's
cabledir 	 = "cable"
def usage():
	print """%s v%s 
Report bugs at http://github.com/jesse-b-semple/
or post it anonymously (perhaps using tor) at:
	http://pastebin.ca  and add a tag "cablegate"
I will search for new posts with that tag regularly

TODO: fix blogger support

USAGE:
<cmd> -upbc --user --password --blogrpc --cablegate

-v|--verbose	off by default, you probably want it on. Though
                it interferes with the poet.
-u|--user       Blog user
-p|--password   Blog password (not recommended, will request
                from prompt instead)
-b|--blogrpc    XMLRPC for users blog
Optional:
-t|--blogtype   "wordpress" or "blogger". Might support others
                Default: wordpress
-i|--blogid     Blog ID if user has multiple blogs. 
                Default: 0 (root blog). 
                Set to "list" to see list of blogs.
-c|--cablegate  The URL of the Wikileaks Cablegate website/index
                Default: %s
                Set to "skip" to skip checking wikileaks for 
                updated cables. This will use the cables in
                cables/ exclusively.
-x|--proxy      http proxy (such as Tor)
-n|--nodamnpoetry  the poet is on by default.

Example using tor:
<cmd> -u jessebsemple -b http://jessebsemple.wordpress.com/xmlrpc.php \\
      -t wordpress -x http://localhost:8118 -v 

To use upload without syncing the cables (if you already downloaded
them from bittorrent or another source) just copy the "cable" dir
into the same directory you run the script from and execute:
<cmd> -u jessebsemple -b http://jessebsemple.wordpress.com/xmlrpc.php \\
      -t wordpress -x http://localhost:8118 -v -c skip

NOTE: proxy only tested with HTTP (not HTTPS). Therefore do not give
a https blog xmlrpc url or https for the cables, until further notice.

Tested on wordpress.org installations and wordpress.com blogs.
	"""%(sys.argv[0], VERSION,  cablegateurl)

support = """
<p><b><a href="%s/support.html">Support Wikileaks</a> and the <a href="https://www.eff.org/support">EFF</a></b></p>
"""%cablegate_prefix 
import zlib, base64
therevolution  = ""
therevolution_ = ""

def progress(n=1):
	if nodamnpoetry:
		return
	global therevolution
	for i in range(0,n):
		if len(therevolution) > 0:
			print therevolution.pop()
		else:
			therevolution = therevolution_
			print "\n\n"
		
def debug(string):
	if VERBOSE:
		print string

# Check proxy
def check_proxy():
	print "\nVerifying proxy"
	print "IP Before proxy use:"
	print BeautifulSoup.BeautifulSoup(urllib.urlopen('http://checkip.dyndns.org', proxies=None).read()).html.body.string
	print "After:"
	print  BeautifulSoup.BeautifulSoup(urllib.urlopen('http://checkip.dyndns.org', proxies=proxy).read()).html.body.string

# Setup blog connection
title_to_ref_re = re.compile("^([^\:]+):")
refs_online = {}
def setup_blog():
	global blog, blogid
	debug("\nConnecting to blog")
	blog = pyblog.WordPress(blogrpcurl, user, password, urlparse.urlparse(proxyurl)[1])
	progress()
	# List blog ids and exit if requested:
	if bloggetlist:
		for b in blogs:
			print "%d: %s"%(blogid, b['blogname'])
		blogid += 1
		sys.exit(2)
	# Find new refs that we do not have yet
	# use tag list with reference_id instead of full page dump
	# faster
	#for post in blog.get_recent_posts(10000000, blogid):
	#	ref =  re.match(title_to_ref_re, post['title'])
	#	if ref:
	#		refs_online.update({ref.group(1): 1})
	for tag in blog.get_tags(blogid):
		refs_online.update({tag['name']: 1})

	progress()
	# check our category exists:
	cats = blog.get_categories(blogid)
	cablegatecat = {
		'name':'Cablegate', # change to 'cablegate'
		'slug':'cablegate',
		'parent_id': 0,
		'description': 'Wikileaks State Department Cables'
		}
	havecat = False
	for c in cats:
		if c['description'] == cablegatecat['name']:
			havecat = True
	if not havecat:
		print "creating category"
		blog.new_category(cablegatecat, blogid)

	

	
def get_cables():
	# Make dirs
	if not os.path.exists(idxdir):
		debug("creating index directory")
		os.mkdir(idxdir)
	if not os.path.exists(cabledir):
		debug("creating cable directory")
		os.mkdir(cabledir)
	
	
	# get all root index files
	debug("\nGetting latest primary index from %s"%cablegateurl)
	progress()
	html        = urllib.urlopen(cablegateurl, proxies=proxy).read()
	soup        = BeautifulSoup.BeautifulSoup(html)
	idxurls     = soup.findAll('a', {'href': re.compile('/'+idxdir+'/.+')})
	for idx in idxurls:
		if os.path.exists(idx['href'][1:]):
			debug("%s: got it, assuming we skip"%idx['href'])
		else:
			debug("%s: getting and storing locally"%idx['href'])
			idxhtml = urllib.urlopen(cablegate_prefix+idx['href'], proxies=proxy).read()
			f = open(idx['href'][1:], 'w')
			f.write(idxhtml)
			f.close()
			progress()
	
	# get pagenated index's within if we dont have them
def get_pages(pageurl):
	debug("\nGetting latest pagenated index's")
	if os.path.exists(pageurl[1:]):
		debug("%s: got it, assuming we skip"%pageurl)
	else:
		debug("%s: getting and storing locally"%pageurl)
		html = urllib.urlopen(cablegate_prefix+pageurl, proxies=proxy).read()
		open(pageurl[1:], 'w').write(html)
		soup = BeautifulSoup.BeautifulSoup(html)
		nextlink = soup.find('div', 'paginator').findAllNext('a')[-1]
		get_pages(nextlink['href'])	
		progress()
	
	for idx in idxurls:
		soup = BeautifulSoup.BeautifulSoup(open(idx['href'][1:]).read())
		nextlink = soup.find('div', 'paginator').findAllNext('a')[-1]
		get_pages(nextlink['href'])
	
	# get all cables
	debug("\nGetting latest cables")
	progress()
	cablestoget = []
	cabledir_re = re.compile('/'+cabledir+'/')
	for idx in os.listdir(idxdir):
		soup = BeautifulSoup.BeautifulSoup(open(os.path.join(idxdir,idx)).read())
		cableurls = soup.findAll('a', {'href': cabledir_re})
		debug(idx)
	progress()
	for cable in cableurls:
		if not os.path.exists(cable['href'][1:]):
			cablestoget.append(cable['href'])
	# Here we should get the index of the blog and check
	# which cables of what we update need to be uploaded
	# This will let us create a progress bar
	for cable in cablestoget:
		debug(cable)
		progress()
		html =  urllib.urlopen(cablegate_prefix+cable, proxies=proxy).read()
		dir = os.path.dirname(cable[1:])
		if not os.path.exists(dir):
			os.makedirs(dir)
		open(cable[1:], 'w').write(html)

# Parse cables
subject_re  = re.compile(".*(SUBJECT|Subject):\s*([^\n]*)", re.MULTILINE | re.DOTALL)
ref_re      = re.compile(".*(REF|Ref):\s*([^\n]*)", re.MULTILINE | re.DOTALL)
ref_re_simp = re.compile("REF:|Ref:", re.MULTILINE | re.DOTALL)
tags_re     = re.compile('TAGS:|Tags:')
tags2a_re   = re.compile('TAGS')
tags2b_re   = re.compile(".*TAGS\s+([^\n]*)", re.MULTILINE | re.DOTALL)
def upload_cable(file):
	f = open(file).read();
	soup = BeautifulSoup.BeautifulSoup(''.join(f))
	part1 = soup.find('pre')
	if not part1:
		debug("ERROR:\t\t%s"%file)
		return
	part2 = part1.findNext('pre')
	if not part2:
		debug("ERROR:\t\t%s"%file)
		return

	links = soup.find('table', { "class" : "cable" }).findAll('a')
	reference_id 	= links[0].string.encode()
	created 		= links[1].string.encode()
	released 		= links[2].string.encode()
	classification 	= links[3].string.encode()
	origin 			= links[4].string.encode() 

	# FIND SUBJECT
	# in some rare cases "Subject:" is used instead of "SUBJECT:"
	subject = ""
	search = part2.find(text=subject_re)
	if search:
		search = re.sub('&#x000A;', "\n", search.string)
		search = subject_re.match(search)
	#	if len(search.group(2)) <= 48:
	#		subject = search.group(2) + search.group(3) 
	#	else:
	#		subject = search.group(2)
		subject = search.group(2)
	if not subject:
		subject = reference_id
	# FIND REFs
	ref = ""
	search = part2.find(text=ref_re_simp)
	if search:
		ref = re.sub('&#x000A;', "\n", search.string)
		ref = ref_re.match(ref).group(2)
	# FIND TAGS
	# Tags can somtimes be referenced with "TAGS:" and links and
	# in rare cases with "TAGS" without links
	tags = []
	tags_ = part2.find(text=tags_re)
	if tags_:
		# assuming all tags are linked with "TAGS:"
		tags_ = tags_.findNextSiblings('a', {'href': re.compile('/tag/')})
		for tag in tags_:
			tags.append(tag.string.encode())
	else:
		# sometimes its just "TAGS"
		tags_ = part2.find(text=tags2a_re)
		if tags_:
			tags_ = re.sub('&#x000A;', "\n", tags_)
			tags_ = tags2b_re.match(tags_)
			if tags_:
				for tag in tags_.group(1).split(','):
					tags.append(re.sub(" ", "", tag))

	#debug("%s\t%s"%(reference_id,subject))
	# Build post 	
	keywords = tags
	keywords.append(reference_id)
	keywords.append(origin)
	keywords.append(classification)
	keywords.append('cablegate')
	keywords.append('wikileaks')
	post = {
			'title': reference_id+': '+subject,
			'description': support+part1.prettify()+part2.prettify(),
			#'dateCreated': ,
			'categories': ['Cablegate'],
			'mt_allow_pings': 1,
			'mt_keywords': keywords,
			}
	progress()
	print "uploading", reference_id,
	id = blog.new_post(post, 1, blogid)
	print id


def upload_cables():
	debug("\nParsing and uploading new cables")
	for root, dirs, files in os.walk(cabledir):
		for file in files:
			if file[-5:] == '.html' and not refs_online.has_key(file[:-5]):
				debug(os.path.join(root, file))
				progress()
				upload_cable(os.path.join(root, file))


def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hu:p:b:t:i:c:x:nv", ["help"
			"user=", 'password=', 'blogrpc=', 'blogtype=', 'blogid=', 'cablegate=',
			"proxy=",  'nodamnpoetry=', 'verbose'])
	except getopt.GetoptError, err:
		print str(err) 
		usage()
		sys.exit(2)
	global user, password, blogrpcurl, blogtype, bloggetlist
	global blogid, cablegateurl, proxyurl, proxy, VERBOSE
	global nodamnpoetry, therevolution, therevolution_
	for o, a in opts:
		if o == "-v":
			VERBOSE = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-u", "--user"):
			user = a
		elif o in ("-p", "--password"):
			password = a
		elif o in ("-b", "--blogrpc"):
			blogrpcurl = a
		elif o in ("-t", "--blogtype"):
			blogtype = a
		elif o in ("-i", "--blogid"):
			if a == "list":
				bloggetlist = True
			else:
				blogid = a
		elif o in ("-c", "--cablegate"):
			if a == "skip":
				cablegateurl = False
			else:
				cablegateurl = a
		elif o in ("-x", "--proxy"):
			proxyurl = a
			proxy = {'http': proxyurl}
		elif o in ("-n", "--nodamnpoetry"):
			nodamnpoetry = True
		else:
			assert False, "unhandled option"
	if not blogrpcurl:
		blogrpcurl   = raw_input("blog xmlrpc url: ")
	if not user:
		user         = raw_input("user: ")
	if not password:
		password     = getpass("password: ")
	if not nodamnpoetry:
		therevolution = zlib.decompress(base64.b64decode("eJy9Vk1v3DYQvfNXzKm5yD6kPbTNyXYTuy6SonEAt0dKml0xS3GEIbWb/fd9Q61jJ84aDlD0ssCKw/l48+YNzxJJ7GmlgVNPsqIxJCZJHVP2oT89PXXuH5lpF2KkJIVaJt9GpiI0xXlNITVUZoWbRB4uOplI5nJ69FaUzLSXWTPHld3KG7+uV/MmTI27wa95oJUo7rFSP2tIa3geR9Yu+Jgbd86dn+GoDEzKW4lzCfD1MGDhyNuQuUcJH55l9oRVqzKvh2IFIHdq9/Q3q3xyvyf6iSavJcO8DJb3fZ4Ap7DqPJm7fNx/HmRX3U6hA5acrRHvwidJro2ys+I9tfMaABpOkX2/fOsGr2u2bK5lSO5tKN3AMTZ0yYkVCZy16sdcb91MQYXO1ol3VgX74gZZ0+h3GSmnVcidL2xUkBGur7xGHkGChJS87p9E55lQPwYR7fshtXl65W5QC6/Q7bOd157gxRdd6r3HqXild774GNjdivSHygpvmd52f83M4KHS+RwjUNsc8LqeY/DH81+H7UJIGtG+gTJ/Ij9N7OMTd7iQhjowxsA0t0+0d/SbGgDUlw2tLNwkc+qzK0NIaFQDcJ5P54bOVWCoC9gAqZrBJMkXDLKQVv8tjgMA8ns3zXkw6pTBV9pNU50s8Jd62aUaH5TrNjaY9qcH10jn1DjgWnRfLwvlGHpevHQS7WjJzpIG6QUEykUi2uHHdo4gEZ+6d+cXjxVhUu6Rcw22q2gQnP78648vLaLyJMitcvLlL9SHXBTWT4D9mI3HAZrCOhsKUqwsA8C1C7QZVdSUQgLpUrFEol+G4P/zdzuEknhPkFL4axleHXpR1RHHhxE14SX1IVYFMqVQ67rN+aTScc7fCJOhK+B7xQ4452JHMazYHL+XvQNpNpxQTlEBfSpn6vjSrS+l1uPpfWVj9OALQrpLtQGMoYX2VM8f53HKcygLU1D+ADa1ZpT91qp5g9gf57y0H9lOaL90nTcioXuLw7MOeDQmCXSOSde4pyuk21Za48CqvQLorFt8Ync9Q7MekAJzl9Zsy4SyUO/HBJlTIwk6Ua+7nYz8gEQYCLRqRb+FzgY2+YiYmPm8TInh7K59XZR0w167oW6rDzKKKoC9G+cFmollQlp36B+YAGAZKmKaYOjafWtdgEDazvPfpbhfNneAk2iO8t0Ym7Vp44vOhtuBG4t0fkW4wQfdk9cRAFVI3H0zMXrLnWvUBDn5M/mcQ6a7DYUk4C7zkjaCjgY3Dh6mvdNQChKxjRVGuuW2bdwb8LWDp5tOSqE/eN/AHJyspN/TpcnIhR+ntq42gOyuJVnjbemlPc7y0NDrhP2IZAtdgXWsWJGbxrht9b+3hr6GzA3/xR6rTaK20n5l3fI0Ysz8ml3b2nB62mF07bmjyffSHP7WniSAVfNavi3k+Oq5NPhtfSvtQCf04+Czl21lj+0q13KvIiPoSyUYuw8HBHm5r3sdTGw+H0mIoFwru6dWm6DEYlVVObmQDR83XlUkaiRWPDTqnI9+Twv/Wxt3xSY/AvuEumxLHUaiV+xGfQHRwZVnvtqaI5/d91h/O7tlmJRPTHPvhPzVMdOI3JHzyQldQoorl0+u8EZM/wLFghCu")).split("\x0a")
		therevolution.reverse()
		therevolution_ = therevolution
		
	#begin 
	if cablegateurl:
		get_cables()
	setup_blog()
	upload_cables()

	


if __name__ == "__main__":
    main()
