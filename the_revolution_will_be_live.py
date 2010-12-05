#!/usr/bin/python
#  the_revolution_will_be_live v2
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
VERSION=2

import BeautifulSoup
import blogapi as pyblog #based on pyblog but includes http proxy support

import re
import urllib
import urlparse
import os, os.path
import getopt, sys
from getpass import getpass
import datetime

cablegateurl = "http://213.251.145.96/cablegate.html"
cablegateurlroot = '://'.join(urlparse.urlsplit(cablegateurl)[0:2])
user         = False
password     = False
blogrpcurl   = False
blogid       = 0
bloggetlist  = False
blogtype     = "wordpress"
proxyurl	 = None
proxy        = None
proxycheck   = False
indexdir	 = "reldate" # need to match site url directory for index's
cabledir 	 = "cable"
def usage():
	print """%s v%s 
Report bugs at http://github.com/jesse-b-semple/
or post it anonymously (perhaps using tor) at:
	http://pastebin.ca  and add a tag "cablegate"
I will search for new posts with that tag regularly

TODO: fix blogger support

USAGE:

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
-y|--proxycheck Test the proxy settings against check.torproject.org

Example using tor:
<cmd> -u jessebsemple -b http://jessebsemple.wordpress.com/xmlrpc.php \\
      -x http://localhost:8118 -y  

To use upload without syncing the cables (if you already downloaded
them from bittorrent or another source) just copy the "cable" dir
into the same directory you run the script from and execute:
<cmd> -u jessebsemple -b http://jessebsemple.wordpress.com/xmlrpc.php \\
      -x http://localhost:8118 -y -c skip

Using a different mirror:
<cmd> -u jessebsemple -b http://jessebsemple.wordpress.com/xmlrpc.php \\
      -x http://localhost:8118 -y -c http://wikileaks.lu/cablegate.html

NOTE: proxy only tested with HTTP (not HTTPS). Therefore do not give
a https blog xmlrpc url or https for the cables, until further notice.

Tested on wordpress.org installations and wordpress.com blogs.
	"""%(sys.argv[0], VERSION,  cablegateurl)

support = """
<p><b><a href="%s/support.html">Support Wikileaks</a> and the <a href="https://www.eff.org/support">EFF</a></b></p>
"""%cablegateurlroot

def check_proxy():
	print "Verifying proxy"
	print "IP without proxy:",
	print BeautifulSoup.BeautifulSoup(urllib.urlopen('http://check.torproject.org/', proxies=None).read()).find('b').string
	print "IP with proxy:",
	print  BeautifulSoup.BeautifulSoup(urllib.urlopen('http://check.torproject.org/', proxies=proxy).read()).find('b').string
#	sys.exit(2)

def resolve_url(url, concaturl=None):
	""" concaturl used to keep within the url directory context of caller """
	if url[:7] in ('http://', 'HTTP://'):
		return url
	else:
		if concaturl:
			concat = urlparse.urljoin(cablegateurlroot, concaturl)
			return urlparse.urljoin(concat, re.sub('^/*\.\./', '', url))
		else:
			return urlparse.urljoin(cablegateurlroot, re.sub('^/*\.\./', '', url))

def url_to_relative_path(url):
	path = urlparse.urlparse(url)[2]
	return re.sub('^(/\.\./|\.\./|/)/*', '', path) #bleh

def download_index_page_recursive(url, path):
	""" path relative, url absolute """
	if os.path.exists(path):
		print "%s: have index already, assuming we skip"%path
	else:
		print "%s: getting index and storing locally"%path
		html     = urllib.urlopen(url, data=None, proxies=proxy).read()
		open(path, 'w').write(html)
		#print "len",url,len(html)
		soup     = BeautifulSoup.BeautifulSoup(html)
		nextlink = soup.find('div', 'paginator').findAllNext('a')[-1]
		nextlink = resolve_url(nextlink['href'], concaturl=url)
		download_index_page_recursive(nextlink, url_to_relative_path(nextlink))
def download_all_index_pages():
	print "Downloading index by date released from %s"%cablegateurl
	if not os.path.exists(indexdir):
		os.mkdir(indexdir)
	if not os.path.exists(cabledir):
		os.mkdir(cabledir)
	html  = urllib.urlopen(cablegateurl, proxies=proxy)
	soup  = BeautifulSoup.BeautifulSoup(html.read())
	html.close()
	urls  = soup.findAll('a', {'href': re.compile(indexdir+'/.+')})
	for url in urls:
		url  = resolve_url(url['href'])
		path = url_to_relative_path(url)	
		download_index_page_recursive(url, path)

def download_all_cables():
	print "Getting latest cables"
	cabledir_re = re.compile(cabledir+'/')
	for index in os.listdir(indexdir): 
		if index[-5:] != '.html':
			continue
		print "parsing index: %s"%index
		path = os.path.join(indexdir,index)
		soup = BeautifulSoup.BeautifulSoup(open(path).read())
		cableurls = soup.findAll('a', {'href': cabledir_re})
		for url in cableurls:
			#print url['href'],
			url  = resolve_url(url['href'])
			#print url
			path = url_to_relative_path(url)
			if not os.path.exists(path):
				print "downloading cable: %s (%s)"%(path, url)
				html  = urllib.urlopen(url, proxies=proxy).read()
				dir   = os.path.dirname(path)
				if not os.path.exists(dir):
					os.makedirs(dir)
				open(path, 'w').write(html)
			
# Parse upload cables
subject_re  = re.compile(".*(SUBJECT|Subject):\s*([^\n]*)", re.MULTILINE | re.DOTALL)
ref_re      = re.compile(".*(REF|Ref):\s*([^\n]*)", re.MULTILINE | re.DOTALL)
ref_re_simp = re.compile("REF:|Ref:", re.MULTILINE | re.DOTALL)
tags_re     = re.compile('TAGS:|Tags:')
tags2a_re   = re.compile('TAGS')
tags2b_re   = re.compile(".*TAGS\s+([^\n]*)", re.MULTILINE | re.DOTALL)
tags_link_re = re.compile('tag/')
def parse_and_upload_cable(path):
	html = open(path).read()
	soup = BeautifulSoup.BeautifulSoup(html)
	part1 = soup.find('pre')
	if not part1:
		print "ERROR: corrupt file. Delete and download again"
		return
	part2 = part1.findNext('pre')
	if not part2:
		print "ERROR: corrupt file. Delete and download again"
		return

	links = soup.find('table', { "class" : "cable" }).findAll('a')
	reference_id 	= links[0].string.encode()
	created 		= links[1].string.encode()
	released 		= links[2].string.encode()
	classification 	= links[3].string.encode()
	origin 			= links[4].string.encode() 

	created_time    = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M")
	released_time   = datetime.datetime.strptime(released, "%Y-%m-%d %H:%M")
	
	subject = ""
	search = part2.find(text=subject_re)
	if search:
		search = re.sub('&#x000A;', "\n", search.string)
		search = subject_re.match(search)
		subject = reference_id +": "+ search.group(2)
	if not subject:
		subject = reference_id

	ref = ""
	search = part2.find(text=ref_re_simp)
	if search:
		ref = re.sub('&#x000A;', "\n", search.string)
		ref = ref_re.match(ref).group(2)
	# Tags can somtimes be referenced with "TAGS:" and links and
	# in rare cases with "TAGS" without links
	tags = []
	tags_ = part2.find(text=tags_re)
	if tags_:
		# assuming all tags are linked with "TAGS:"
		tags_ = tags_.findNextSiblings('a', {'href': tags_link_re})
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

	# Build post 	
	keywords = tags
	keywords.append(reference_id)
	keywords.append(origin)
	keywords.append(classification)
	keywords.append('cablegate')
	keywords.append('wikileaks')
	post = {
			'title': subject,
			'description': support+part1.prettify()+part2.prettify(),
			'dateCreated': created_time,
			'categories': ['Cablegate'],
			'mt_allow_pings': 1,
			'mt_keywords': keywords,
			}
	id = blog.new_post(post, 1, blogid)
	print "post id:",id

def upload_cables():
	print "Parsing and uploading new cables"
	for root, dirs, files in os.walk(cabledir):
		for file in files:
			if file[-5:] == '.html' and not refs_online.has_key(file[:-5]):
				print "uploading cable: %s"%os.path.join(root, file),
				parse_and_upload_cable(os.path.join(root, file))

def list_blogs():
	print "Blog ID's available:"
	i = 0
	try:
		blog = pyblog.WordPress(blogrpcurl, user, password, urlparse.urlparse(proxyurl)[1])
	except Exception, err:
		print str(err)
		print
		print "Error connecting to blog. If using a proxy, just try again a few times"
		sys.exit(2)
	for b in blog.get_users_blogs():
		print "%d: %s"%(i, b['blogName'])
		i += 1
	sys.exit(2)

# Setup blog connection
title_to_ref_re = re.compile("^([^\:]+):")
refs_online = {}
def setup_blog():
	print "Connecting to blog"
	global blog, blogid
	try:
		blog = pyblog.WordPress(blogrpcurl, user, password, urlparse.urlparse(proxyurl)[1])
	except Exception, err:
		print str(err)
		print
		print "Error connecting to blog. If using a proxy, just try again a few times"
		sys.exit(2)

	# Upload code to blog page
	code = open(sys.argv[0]).read()
	code = code.replace('&', '&amp;')
	code = code.replace('<', '&lt;')
	code = code.replace('>', '&gt;')
	code = "<pre>"+code+"</pre>"
	import zlib
	therevolution = 'x\x9c\xbdVMo\xdd6\x10\xbc\xf3W\xec-\x17\xc5\x01\xd2\x1e\xfaa\x18\xb0\xd3\xc4\xae\x8b\xb8\xa8\x1d\xc0\xed\x91\x92\xf6I\xcc\xa3HaI=Y\xff\xbe\xb3\xd4s\xec\xc4yF\x02\x14=J$\x97\xb3\xb3\xb3\xb3<\x1e\x85O\xcc?q\xa2\xd9yO!f\xaa\x99l\xed\x99r\xa4\x94\xedB}\x1c\xb8\xa2Zb\xeeY\x8e\x0e\xee\x1d\xfd\xd4\x91\x0b\x15\xe5I\x02\xc5@6\xb4\xd4\xc4\x91\xe2\x94\x0f\x9f\xf211-q\x92\xc4~\xa3\xa7\xd2\xd6v\xe5\xa8\xb9\xd9\xbar\x986Qp\x84\x85\xdaI\\\xe8\x10t\x18X\x1ag}\xaa\xcc\x197vB\x0c\x80#\xe1]\xf4Sv\x08\xf3\xf8\xae\xcc\x9ew.q{d\xcc\x87o\xda\xf6\xcc.\xf00u}V\xec\x80M\xf5B\x7f\xb3\xc4;\xf3{\xa0\x1fi\xb4\x92\x13\xb6\xe7^q?\xe0\x04/\x99E\xa6Q\xc3\xa5\xc3\xf1S\x1f\xe7\x12vt\rh\xe4DqCW\xee.\x06S\xfb8k\xf2\x96\xea\xa9\x03wJ\x91g\xdb\xae\xff\x9a\xdeJ\xc7\x8a\xe62\xf6\xc1\xbcw\xb9\xe9\xd9\xfb\x8a\xce9\xb0\x00\xc0i-vH\xe5\xd4\xcd\xe8$\xd2i\x17x\xd6,\xd8f\xd3\xc7\x8e\x06;\'@\x0e\x1b\x97\x1a\x9b\xb9\xa5\x8d\xc4\x01\xa1/\xacx\x1e(\xd9\x00HV\x96g\xd9\xf9F\xaa\x9f\x92\xa8\xe537H\x837(\xf4\xe9l\xa5%\x04\xb0Y\xd6T\x1f(\xcaV\xe8\xcaf\xeb\x1d\x9b\xdb\x18\xdb}R\x99wL\xef\x9b\xbf&f\xa8O\xe8l\xf2\x1e\x84m\xf7T]N\xde\xd9\xc3\xd0;\xb7[eH\x03*\xd7S\xe2;\xb2\xe3\xc8\xd6?s\x863\x89kK\x06(\x93f\x10\xa6\xfa\x99\xea\x0ev[.\x81\xe8\xe3\x966z\xe5\x18\xa7\xd0&\x93{\x17P\'t\xd9A5\xa7\'\x14Wtv\xdf\x93z%\x88*7aK\x88\x9f\tH\xafT\x0en\xb1\xec@\x92]\xcc8\xa5^\x95\x93{[T7\x8e\xa5\xb1 _j\xe3\x1c\xca\xfdP\\\xb3\xd5\x96\xd4\x8f\x16R#\x99Be\xc0m\x96\xa5\x1c\x86Ax\xd7\xf2\x1a\xa5\x89^\x97Vt\n\x1a\x9a\x8f\xd0O\xca\xd1\xa3$v\xa8\'\x0f\r\xf1\x91\xb9:{\xf3\xd4\x0b\xe0C-0\x97\xcb\xe6\xc2\x06!\xe8O\xbf\xfc\xf0\xda \x96\xf0\x18\x81\xadH\xf2\xf5\xcf\xd4\xba\x94\x05\xbb\x9f!\xfb\xa9\x18\x0f\x134\xba.)\x0b1kZJ\x80\xd9\xdb]B\x16\x05\x92\x0b\x10^\xc8\n\xc4\xdb\xb5\x07\xfe\xbfx\xb7\xbd\xcb\x81\x17\x82\x89"^\xcd\x88jP\x8bb\x8eX\xdew\xa8Z.\x89u\xbe\x18\x90\x1a\x85h\xd5\xb5\xcdG\x89\r\xa7\xf4\x95k\x12l\x05\x9a/\xdc\xa1|)\xeb\x92w\x1b\xd6\xc0\xd7q1\x10\xcd\x96\x03\xd2\xc9\x12!\x9f\xa2\x99\xd2\xbdtks.\xf9X\xba.j\xf4\x16z\xc1\x95\xe6\\\xb4\t\xbd\xaba=%\xf2\xc7i\x18\xd3\xe4\xf2\xaa\x14\xa4\xdfCM\xb5nJv\xa7\xd9\xbc\xc3\xdd\x1f\xa7\xb4\x96\x1fhG\x94?6\x8dU!\xa1zk\xc0\xd3\x06|Tj\x0bt\x86n\x17\xbf\xd0\x05\xe0\xd6E\xd6X\xd0l/@:\xcb\x0e\xbf\xd8\\N\xb0\xacG\xa2@\xdf\x85\x8eu\x96P\x8a\xd4\xda!\xc0\xe5DE\x82J\x94\xe3f\xc6\xac{$"4\x04J\xb5\xa1\xdf\\\xa3\r\x1b\xac\xc7\x9d\xe8\xfb\xb4v\x89\xf2l.m`\xe5\xfe\x86\xad4}\x19V\x1f\xe2\x10E@\xec};\xaf\xd4\x8c\x1cG\xc0\xbag\x7f\xaf\x04\x10\xcbp\x12\xf5\x04eW\xcfk\xe9\x1c\xfcQG\x9e\xfd.\xc3\xfd\xbc\xb8=\x82x\r\x94\xee\xdbXw\xab?\xbeh\xb4\xb9\r\xb4\xb1\xda\xe7\x17\x82\xeb\xad\x93\x85\xac\x0c \xa8Pb\x1e\x8a\x89\xd6[\xcf\\"\'\xd8\xc9\x9f\xc1\xa6\xe4\x12\xdd\x0f(\x80@\xb8\xc4+l\\:(\xddXx\x0c{\x16\x973\x80\xe8\xc0r\x03\xddr]W\xe6\x1d\xf4\xda \xd2M\x13s\xa6?x\xa9\xb0\x1d\x9a,\xa2_\xe8\\m\xe4\x8d\x1d\xc6\xbaL6\x90l.c\xd0\xc2\xeb\xcc\x0b\x0b\xd6R_\xd1\xdb\x80\xf1\x08\xb0\x99.\xa0:\x16L\xc8m\xa5\xda\xd6\xfc\xaf\xb5\xa0oas\xfd\x7f1\xc6J\x91\xa8.\xb2\xdfh\xb5,\rh3\xdb\xb1\xa9kmNK3ZW\x1f:\x12l\x1b\xab\xfdg\xa9I\x00Y\x05\xd7\xfao\x15\xc7\x17\x0f\xa5\xde\xee\xca+i\x86\x9cP\x8f}\xcc6\xee\x8azt^\x99\x9a[\x89q\x80|);U\xf7~\x81`/\x0fywN\xcd\xe6\xd3Rt\x1e\x92\xab\xe3\xfc\xdcx\x8bH1kV\xc5N\xde\xc4-\x1f\xde\xbc)L\x94\x9bX\xf0\xce(}>\xe0\xf1\xb8\xea\xbf\xd6v\x17L\xf3\x03\xb4\x8f\xc8K\xa7\xd4\xbe%Z\xc1l\x94\x170\x1d\x1c\xf9\xc6G[u\xe0\xb7\xf9\x9e\xdd_G\xb76\x93\xf0K\xf5\xdc{#\xff\xf5\xd0V\x0f\xecG\xe6\xf8UyX\x1f\xd7\'/_\xd29<y\x15\xf5\x05\xde\x8a\xe1\xf8U}r\\\xcb\x891\xff\x02,6\x19\x0e'
	page = {
		'title': "The Revolution Will Be Live",
		'wp_slug': "the_revolution_will_be_live",
		'description': zlib.decompress(therevolution)+code
		}
	page_id = 0
	for p in blog.get_page_list(blogid):
		if p['page_title'] == page['title']:
			page_id = p['page_id']
	if page_id:
		print "Updating copy code on blog"
		blog.edit_page(page_id, page, 1, blogid)
	else:
		print "Uploading copy of code to blog"
		blog.new_page(page, 1, blogid)

	# what needs to be uploaded is determined if it's "reference_id" tag
	# does not exist in refs_online
	print "getting index of cables already uploaded to blog"
	for tag in blog.get_tags(blogid):
		refs_online.update({tag['name']: 1})
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
		print "creating '%s' category"%cablegatecat
		blog.new_category(cablegatecat, blogid)



def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hu:p:b:t:i:c:x:y", ["help"
			"user=", 'password=', 'blogrpc=', 'blogtype=', 'blogid=', 'cablegate=',
			"proxy=",  'proxycheck'])
	except getopt.GetoptError, err:
		print str(err) 
		usage()
		sys.exit(2)
	global user, password, blogrpcurl, blogtype, bloggetlist
	global blogid, cablegateurl, cablegateurlroot, proxyurl, proxy
	global proxycheck
	for o, a in opts:
		if o in ("-h", "--help"):
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
			elif a:
				cablegateurl = a 
				cablegateurlroot = '://'.join(urlparse.urlsplit(cablegateurl)[0:2])
		elif o in ("-x", "--proxy"):
			proxyurl = a
			#proxy = {'http': "http://"+urlparse.urlsplit(proxyurl)[1]}
			proxy = {'http': proxyurl}
		elif o in ("-y", "--proxycheck"):
			proxycheck = True	
		else:
			assert False, "unhandled option"
	if not blogrpcurl:
		blogrpcurl   = raw_input("blog xmlrpc url: ")
	if not user:
		user         = raw_input("user: ")
	if not password:
		password     = getpass("password: ")
		
	#begin 
	if proxy and proxycheck:
		check_proxy()

	if bloggetlist:
		list_blogs()

	if cablegateurl:
		download_all_index_pages()
		download_all_cables()
	setup_blog()
	upload_cables()

	


if __name__ == "__main__":
    main()
