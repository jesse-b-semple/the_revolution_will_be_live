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
	code = code.replace('<', '&lt;')
	code = code.replace('>', '&gt;')
	code = "<pre>"+code+"</pre>"
	import zlib
	therevolution = 'x\x9c\xbdVMo\xdc6\x10\xbd\xf3W\xcc-\x17\xc5\x05\xd2\x1e\xfaa\x04\xb0\xd3\xc4\xae\x8b\xb8\xa8\x1d\xc0\xed\x91\x92f%f)R\x18R+\xeb\xdf\xf7\r\xb5\xae\x9d8\xbbH\x80\xa2G\x89\xe4\xf0\xcd\x9b7ox:\n\xbf6\x7f\xc7\x89f\xe7=\x85\x98\xa9f\xb2\xb5g\xca\x91R\xb6\x0b\xf5q\xe0\x8aj\x89\xb9g99\xb8w\xf4SG.T\x94\'\t\x14\x03\xd9\xd0R\x13G\x8aS>|\xca\xc7\xc4\xb4\xc4I\x12\xfb\x8d\x9eJ[\xdb\x95\xa3\xe6v\xeb\xcaa\xdaD\xc1\x11\x16j\'q\xa1C\xd0a`i\x9c\xf5\xa92\xe7\xdc\xd8\t1\x00\x8e\x84w\xd1O\xd9!\xcc\xd3\xbb2{\xde\xb9\xc4\xed\x891\x1f\xbej\xdb\x91]\xe0a\xea\xfa\xac\xd8\x01\x9b\xea\x85\xfeb\x89\xf7\xe6\xb7@?\xd0h%\'l\xcf\xbd\xe2~\xc4\t^2\x8bL\xa3\x86K\x87\xe3\xa7>\xce%\xec\xe8\x1a\xd0\xc8\x89\xe2\x86\xae\xdd}\x0c\xa6\xf6q\xd6\xe4-\xd5S\x07\xee\x94"\xcf\xb6]\xff5\xbd\x95\x8e\x15\xcdU\xec\x83y\xefr\xd3\xb3\xf7\x15]p`\x01\x80\xb3Z\xec\x90\xca\xa9\xdb\xd1I\xa4\xb3.\xf0\xacY\xb0\xcd\xa6\x8f\x1d\rvN\x80\x1c6.56sK\x1b\x89\x03B_Z\xf1<P\xb2\x01\x90\xac,G\xd9\xf9J\xaa\x9f\x93\xa8\xe53\xb7H\x837(\xf4\xd9l\xa5%\x04\xb0Y\xd6T\x1f)\xcaV\xe8\xdaf\xeb\x1d\x9b\xbb\x18\xdb}R\x99wL\xef\x9b?\'f\xa8O\xe8|\xf2\x1e\x84m\xf7T]M\xde\xd9\xc3\xd0;\xb7[eH\x03*\xd7S\xe2{\xb2\xe3\xc8\xd6\x1f9\xc3\x99\xc4\xb5%\x03\x94I3\x08S}\xa4\xba\x83\xdd\x96K \xfa\xb8\xa5\x8d^9\xc6)\xb4\xc9\xe4\xde\x05\xd4\t]vP\xcd\xe9\x19\xc5\x15\x9d?\xf4\xa4^\t\xa2\xcaM\xd8\x12\xe2\'\x02\xd2+\x95\x83;,;\x90d\x173N\xa9W\xe5\xe4\xde\x16\xd5\x8dci,\xc8\x97\xda8\x87r?\x14\xd7l\xb5%\xf5\xa3\x85\xd4H\xa6P\x19p\x9be)\x87a\x10\xde\xb5\xbcFi\xa2\xd7\xa5\x15\x9d\x82\x86\xe6#\xf4\x93r\xf4(\x89\x1d\xea\xc9CC|b\xae\xcf\xdf<\xf7\x02\xf8P\x0b\xcc\xe5\xb2\xb9\xb0A\x08\xfa\xe3\xcf\xdf\xbf2\x88%<F`+\x92|\xf5\x13\xb5.e\xc1\xee#d?\x17\xe3a\x82F\xd7%e!fMK\t0{\xbbK\xc8\xa2@r\x01\xc2\x0bY\x81x\xbb\xf6\xc0\xff\x17\xef\xaew9\xf0B0Q\xc4\xab\x19Q\rjQ\xcc\x11\xcb\xfb\x0eU\xcb%\xb1\xce\x17\x03R\xa3\x10\xad\xba\xb6\xf9(\xb1\xe1\x94\xbepM\x82\xad@\xf3\x85;\x94/e]\xf2n\xc3\x1a\xf8&.\x06\xa2\xd9r@:Y"\xe4S4S\xba\x97\xeel\xce%\x1fK7E\x8d\xdeB/\xb8\xd2\\\x886\xa1w5\xac\xa7D\xfe8\rc\x9a\\^\x95\x82\xf4{\xa8\xa9\xd6M\xc9\xee4\x9bw\xb8\xfb\xe3\x94\xd6\xf2\x03\xed\x88\xf2\xc7\xa6\xb1*$To\rx\xd6\x80\x8fJm\x81\xce\xd1\xed\xe2\x17\xba\x04\xdc\xba\xc8\x1a\x0b\x9a\xed%Hg\xd9\xe1\x17\x9b\xab\t\x96\xf5D\x14\xe8\xbb\xd0\xb1\xce\x12J\x91Z;\x04\xb8\x9c\xa8HP\x89r\xdc\xcc\x98uOD\x84\x86@\xa96\xf4\xabk\xb4a\x83\xf5\xb8\x13}\x9f\xd6.Q\x9e\xcd\x95\r\xac\xdc\xdf\xb2\x95\xa6/\xc3\xeaC\x1c\xa2\x08\x88}h\xe7\x95\x9a\x91\xe3\x08X\x0f\xec\xef\x95\x00b\x19N\xa2\x9e\xa0\xec\xeay-\x9d\x83?\xea\xc8\xb3\xdfd\xb8\x9f\x16\xb7G\x10\xaf\x81\xd2C\x1b\xebn\xf5\xc7\x17\x8d6\xb7\x816V\xfb\xfcLp\xbdu\xb2\x90\x95\x01\x04\x15J\xccc1\xd1z\xeb\x99+\xe4\x04;\xf9#\xd8\x94\\\xa2\x87\x01\x05\x10\x08\x97x\x85\x8dK\x07\xa5\x1b\x0bOa\xcf\xe2r\x06\x10\x1dXn\xa0;\xae\xeb\xca\xbc\x83^\x1bD\xbamb\xce\xf4;/\x15\xb6C\x93E\xf4\x0b]\xa8\x8d\xbc\xb1\xc3X\x97\xc9\x06\x92\xcdU\x0cZx\x9dya\xc1Z\xea+z\x1b0\x1e\x016\xd3%T\xc7\x82\t\xb9\xadT\xdb\x9a\xff\x8d\x16\xf4-l\xae\xff/\xc6X)\x12\xd5E\xf6\x1b\xad\x96\xa5\x01mf;6u\xad\xcdiiF\xeb\xeaCG\x82mc\xb5\xff,5\t \xab\xe0Z\xff\xad\xe2\xf8\xec\xa1\xd4\xdb]y%\xcd\x90\x13\xea\xb1\x8f\xd9\xc6]Q\x8f\xce+Ss+1\x0e\x90/e\xa7\xea\xde/\x10\xec\xe51\xef\xce\xa9\xd9\xfc\xbb\x14\x9d\x87\xe4\xea8\x1f\x1bo\x11)f\xcd\xaa\xd8\xc9\x9b\xb8\xe5\xc3\x9b7\x85\x89r\x13\x0b\xde\x19\xa5\xcf\x07<\x1eW\xfd\xd7\xda\xee\x82i~\x80\xf6\x11y\xe9\x94\xda\xb7D+\x98\x8d\xf2\x02\xa6\x83#_\xf9h\xab\x0e\xfc6\xdf\xb2\xfb\xcb\xe8\xd6f\x12~\xa9\x9e\xfb`\xe4\xbf\x1c\xda\xea\x81\xfd\xc4\x9c~W\x1e\xd6\xa7\xf5\xeb\x97/\xe9\x02\x9e\xbc\x8a\xfa\x12o\xc5\x80\x9f\xa7\xb5\xbc6\xe6\x1f\x13\xb2\x18\xdf'
	page = {
		'title': "The_Revolution_Will_Be_Live",
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
