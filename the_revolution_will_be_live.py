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
