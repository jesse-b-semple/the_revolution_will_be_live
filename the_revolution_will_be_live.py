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
import contextlib
def download_index_page_recursive(url, path):
	""" path relative, url absolute """
	if os.path.exists(path):
		print "%s: have index already, assuming we skip"%path
		return

	print "%s: getting index and storing locally"%path
	with contextlib.closing(urllib.urlopen(url, data=None, proxies=proxy)) as h:
		html = h.read()	
		print html
	#html     = urllib.urlopen(url, data=None, proxies=proxy).read()
	open(path, 'w').write(html)
	#print "len",url,len(html)
	try:
		soup     = BeautifulSoup.BeautifulSoup(html)
		nextlink = soup.find('div', 'paginator').findAllNext('a')[-1]
	except Exception, err:
		print err
		print "\nProblem parsing %s. Exiting. Delete reldata indexes"%path
		print "and try again. Corrupt indexes appear at times when"
		print "using a proxy."
		print url
		sys.exit(2)
	nextlink = resolve_url(nextlink['href'], concaturl=url)
	path = url_to_relative_path(nextlink)
	if not os.path.exists(path):
		download_index_page_recursive(nextlink, path)
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
	try:
		soup = BeautifulSoup.BeautifulSoup(html)
	except Exception, err:
		print "ERROR: cannot parse file. Deleted."
		print "Deleted. Rerun to download again."
		os.remove(path)
		return
	part1 = soup.find('pre')
	if not part1:
		print "ERROR: corrupt file. Deleted. "
		print "Rerun to download again."
		os.remove(path)
		return
	part2 = part1.findNext('pre')
	if not part2:
		print "ERROR: corrupt file. Deleted."
		print "Rerun to download again."
		os.remove(path)
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
	#print part1.contents[0]
	post = {
			'title': subject,
			'description': support+part1.prettify()+part2.prettify(),
			#'description': support+part1.contents[0]+part2.contents[0],
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
		print "Error connecting to blog. If using a proxy,"
		print "try again a few times, use a different proxy,"
		print "or help us improve the code"
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
	therevolution='x\x9c\xbdVMo\xdc6\x10\xbd\xf3W\x0crI\x0b\xec\xda@\xdaC\x9bn\r\xd8ib\xd7E\\46\xea\xf6\x14P\xd2\xec\x8aY\x8aT\x87\xd4\xca\xfb\xef\xfb\x86\xda\x8d\x938k$@\xd1\xa3\xc4\xe1|\xbcy\xf3\x86\x0bK\xad\xf0\xf2\xe7\'m\xce\xfd\xf3\xe3\xe3q\x1c\x8f\x1a\xeb\xfc\xb6\x8b\xd9\xc5pT\xc7\xeex\xe3\x1a\x8e\xc7w\xfd?C~\x9b[\x9e\x0bo\xa2\x1f\xf4x>:\xef\xe7!\xe6y\xc5\xf3\xcc\x9e7.\xf1\xdbnH\xae~rr\xd32\xbdyoJ\xb70\xa5\xab\x98\xe9\x8c\xe9fg\xda\xd07\x7f\xaa\xf3o\x17\xc7\xf6\xc4,z\xe1\x13\xf3w\x1cH\xdd\x12\xdcR\xc5d+\xcf\x94#\xa5l\xb7\xd4\xc6\x8egTID\x1ert\xd0\xb6\xf7\xc3\x8a\\\x98Q\x1e$\x10\x82\xdb\xd0P\x1d{\x8aC>|\xcb\xc7\xc4\xb4\x8d\x83$\xf6K\xbd\x95\xd6vU\xae\x9a\xeb\xb5+\x97i\x19\x05WX\xa8\x19\xc4\x85\x15\x9cv\x1dK\xed\xacO3s\xc6\xb5\x1d\xe0\x03\xc9\xd1=H\x1f\xc5\xda\x83\xd4\x1c\x19s\xf3Ef\x8fX\x01\x87a\xd5f\xcd\x1diS\xb5\xa5\xbfX\xe2\x9d\xf95\xd0\xf7\xd4[\xc9\t\xe6\xb9\xd5\xbc\xef\xf3\x04.\x99E\x86^\xdd\xa5\xc3\xfeS\x1b\xc7\xe2\xb6w5`\xe4DqIW\xee.\x06S\xf98j\xf1\x96\xaaa\x05\xec\x14"\xcf\xb6\x99\xfe\xd5\xad\x95\x15k6\x97\xb1\r\xe6\xb5\xcbu\xcb\xde\xcf\xe8\x9c\x03\x0b\x128\xad\xc4v\xa9\xdc\xba\xee\x9dD:]\x05\x1e\xb5\n\xb6\xd9\xb4qE\x9d\x1d\x13R\x0eK\x97j\x9bA\x93\xa5\xc4\x0e\xae/\xacx\xee(\xd9\x80\x94\xacl\x1fE\xe7\x0b\xa1~\x08\xa2\xb6\xcf\\\xa3\x0c^\xa2\xd1\xa7\xa3\x95\x86\xe0\xc0f\x99J\xbd\x87([\xa1+\x9b\xadwlnclvEe\xde0\xbd\xae\xff\x18\x98\xc1>\xa1\xb3\xc1{\x00\xb6\xdeAu9xg\x0f\xa7\xber\x9b\x89\x86\xd4\xa1s-%\xbe#\xdb\xf7l\xfd#w8\x93\xb8\xa6T\x806i\x05a\xa8\x1e\xe9ng\xd7%\x08H\x1f\xd7\xb4\xd4\x90}\x1cB\x93Ln]@\x9f0e\x07\xd9\x9c\x1e@<\xa3\xb3\xfdLjH\x00U"\xc1$\xc4\x8f\x08\xa4!\x15\x03U\x03\x07\x90\xec\xd6\xf4Cj\x959\xb9\xb5\x85u}_\x06\x0b\xf4\xa5&\x8e\xa1\xc4\x07\xe3\xea\xb5\x8e\xa4~4\xa0\x1a\xc9\x10f\x06\xd8f\xd9\x96\xcb\x10\x08\x0f)\x99\xbc\xd4\xd1\xeb\xd1\x94\x9d&\r\xceG\xf0\'\xe5\xe8\xd1\x12\xdbU\x83\x07\x87\xf8\xc8\\\x9d\xbdx\xa8\x05\xd0\xa1\x069\x97`cA\x83\xe0\xf4\x87\xe7\xdf=3\xf0%\xdcG\xe4V(\xf9\xecGj\\\xca\x02\xebG\xc0~H\xc6\xc3\x00\xf5n\x95\x14\x05\xc8/\xcaR\x00\xccN\xee\x12\xaa()\xb9\x00\xe2\x85\xac\x89x;\xcd\xc0\xff\xe7\xef\xb6u9\xf0\x96 \xa2\xf0W1\xbc\x1a\xf4\xa2\x88#\x8ew\x13\xaa\x92K\x82=R\x04H\x85B\xb4\xeb:\xe6\xbd\xc4\x9aS\xfaL\x98\x04Y\xa1i\xef\xe8\xd4\xa4\xacG\xde-Y\x1d\xbf\x89[\x03\xd2\xac9\xa0\x9c,\x11\xf4)\x9c)\xd3K\xb76\xe7R\x8f\xc5\xcaQ6z\x0b\xbe \xa49\x17\x1dB\xef*HO\xf1\xfcn\xe8\xfa4\xb8<1\x05\xe5\xb7`S\xa5F\xc9n\xb4\x9aW\x88\xfdnHS\xfb\x91m\x8f\xf6\xc7\xba\xb6J$torxZ\x03\x8f\x99\xca\x02\xf6\xd9\x86\xc5o\xe9\x02\xe9V\x85\xd68\xd0j/\x00:\xcb\x06\xbf\xd8\\\x0e\x90\xac\x0fH\x81\xb9\x0b+\xd6]B)Rc\xbb\x00\x95\x13%\t:Q\xae\x9b\x11\xbb\xee\x03\x12a \xd0\xaa%\xfd\xe2j\x1d\xd8`=bb\xee\xd34%\x8a\xb3\xb9\xb4\x81\x15\xfbk\xb6R\xb7eY\xdd\xc4.\x8a\x00\xd8\xfd8O\xd0\xf4\x1c{\xa4\xb5G\x7f\xc7\x04\x00\xcbP\x12\xd5\x04EW\xefk\xeb\x1c\xf4QW\x9e\xfd*\xc1\xfd\xb8\xb9-\x9cxu\x94\xf6c\xac\xd6\xaa\x8fOk\x1dn\x03nL\xf2\xf9\t\xe1Z\xebdKV:\x00T 1\xf7\xcd\xc4\xe8Mw.Q\x13\xe4\xe4\xf7`Sr\x89\xf6\x0b\nI\xc0]\xe2)m\x04\xed\x14n\x1c|\x98\xf6(.g$\xa2\x0b\xcbut\xcbU53\xaf\xc0\xd7\x1a\x9e\xae\xeb\x983\xfd\xc6\xdb\x19\xcc\xc1\xc9B\xfa-\x9d\xab\x8c\xbc\xb0]_\x95\xcd\x06\x90\xcde\x0c\xdax\xddya\x8b\xb3\xd4\xce\xe8e\xc0zD\xb2\x99.\xc0:\x16l\xc8\xf5L\xb9\xad\xf5\xbf\xd1\x86\xbe\x84\xcc\xb5\xff\xc5\x1a+M\xa2\xaa\xd0~\xa9\xdd\xb2\xd4a\xcc\xec\x8aMU\xe9pZ\x1a1\xba\xfa\xd0\x91`\x9b8\xdb}\x96\x9e\x04\x80U\xf2\x9a\xfeM\xe4\xf8\xe4\xa1\xd4\xdaMy%\x8d\xa0\x13\xfa\xb1\xf3\xd9\xc4Ma\x8f\xee+Sq#1v\xa0/e\xa7\xec\xde\x1d\x10\xe4\xe5\xbe\xee\x95S\xb1y\x7f\x14\x9d\x07\xe5\xaa8>\xb6\xde"J\xccZU\x91\x93\x17q\xcd\x87\x8d\x97\x05\x89\x12\x89\x05\xef\x8c2\xe7\x1d\x1e\x8f\x13\xff+\x1dw\xc16?\x00{\x8f\xbatK\xedF\xa2\x11\xecFy\n\xd1\xc1\x95/|\xb4\xcd\x0e\xfc6_c\xfd\xf9\xec\xa6a\x12<\xc2\xa1\xb9{!\xff\xe9\x90\xa9G\xeeGfq\\\x1e\xd6\x8b\xead>\xa7sh\xf2D\xea\x0b\xbc\x15\xc3\xe2\xb8:YTrb\xcc\xbf\xd5mK\xf9'
	page = {
		'title': "The Revolution Will Be Live",
		'wp_slug': "the_revolution_will_be_live",
		'description': "<b>Dec 19th, cableleaksweap day</b><br>Get a copy of this code and upload the cablegate files to a blog of your choice on that day<br><br"+zlib.decompress(therevolution)+code
		#'description': code
		}
	page_id = 0
	for p in blog.get_page_list(blogid):
		if p['page_title'] == page['title']:
			page_id = p['page_id']
	if page_id:
		print "Updating code copy on blog"
		blog.edit_page(page_id, page, 1, blogid)
	else:
		print "Uploading copy of code"
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
