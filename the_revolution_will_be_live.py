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
import zlib, base64
import gzip, io

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

cat_cablegate_id=0
cat_tag_id=0
cat_embassy_id=0
cat_classification_id=0

support = '<p><b><a href="%s/support.html">Support Wikileaks</a>, '\
'<a href="http://couragetoresist.org/bradley/">Bradley Manning\'s Freedom</a> '\
'and the <a href="https://www.eff.org/support">EFF</a></b></p>'

therevolution = 'eJy9Vk1v3DYQvfNXDHJJC+zaQNpDm24N2Gli10VcNDbq9hRQ0uyKWYpUh9TK'\
'++/7htqNkzhrJEDRo8ThfLx584YLS63w8ucnbc798+PjcRyPGuv8tovZxXBU'\
'x+544xqOx3f9P0N+m1ueC2+iH/R4Pjrv5yHmecXzzJ43LvHbbkiufnJy0zK9'\
'eW9KtzClq5jpjOlmZ9rQN3+q828Xx/bELHrhE/N3HEjdEtxSxWQrz5QjpWy3'\
'1MaOZ1RJRB5ydNC298OKXJhRHiQQgtvQUB17ikM+fMvHxLSNgyT2S72V1nZV'\
'rprrtSuXaRkFV1ioGcSFFZx2HUvtrE8zc8a1HeADydE9SB/F2oPUHBlz80Vm'\
'j1gBh2HVZs0daVO1pb9Y4p35NdD31FvJCea51bzv8wQumUWGXt2lw/5TG8fi'\
'tnc1YOREcUlX7i4GU/k4avGWqmEF7BQiz7aZ/tWtlRVrNpexDea1y3XL3s/o'\
'nAMLEjitxHap3LrunUQ6XQUetQq22bRxRZ0dE1IOS5dqm0GTpcQOri+seO4o'\
'2YCUrGwfRecLoX4IorbPXKMMXqLRp6OVhuDAZplKvYcoW6Erm613bG5jbHZF'\
'Zd4wva7/GJjBPqGzwXsAtt5BdTl4Zw+nvnKbiYbUoXMtJb4j2/ds/SN3OJO4'\
'plSANmkFYage6W5n1yUISB/XtNSQfRxCk0xuXUCfMGUH2ZweQDyjs/1MakgA'\
'VSLBJMSPCKQhFQNVAweQ7Nb0Q2qVObm1hXV9XwYL9KUmjqHEB+PqtY6kfjSg'\
'GskQZgbYZtmWyxAIDymZvNTR69GUnSYNzkfwJ+Xo0RLbVYMHh/jIXJ29eKgF'\
'0KEGOZdgY0GD4PSH5989M/Al3EfkVij57EdqXMoC60fAfkjGwwD1bpUUBcgv'\
'ylIAzE7uEqooKbkA4oWsiXg7zcD/5++2dTnwliCi8FcxvBr0oogjjncTqpJL'\
'gj1SBEiFQrTrOua9xJpT+kyYBFmhae/o1KSsR94tWR2/iVsD0qw5oJwsEfQp'\
'nCnTS7c251KPxcpRNnoLviCkORcdQu8qSE/x/G7o+jS4PDEF5bdgU6VGyW60'\
'mleI/W5IU/uRbY/2x7q2SiR0b3J4WgOPmcoC9tmGxW/pAulWhdY40GovADrL'\
'Br/YXA6QrA9IgbkLK9ZdQilSY7sAlRMlCTpRrpsRu+4DEmEg0Kol/eJqHdhg'\
'PWJi7tM0JYqzubSBFftrtlK3ZVndxC6KANj9OE/Q9Bx7pLVHf8cEAMtQEtUE'\
'RVfva+sc9FFXnv0qwf24uS2ceHWU9mOs1qqPT2sdbgNuTPL5CeFa62RLVjoA'\
'VCAx983E6E13LlET5OT3YFNyifYLCknAXeIpbQTtFG4cfJj2KC5nJKILy3V0'\
'y1U1M6/A1xqeruuYM/3G2xnMwclC+i2dq4y8sF1flc0GkM1lDNp43Xlhi7PU'\
'zuhlwHpEspkuwDoWbMj1TLmt9b/Rhr6EzLX/xRorTaKq0H6p3bLUYczsik1V'\
'6XBaGjG6+tCRYJs4232WngSAVfKa/k3k+OSh1NpNeSWNoBP6sfPZxE1hj+4r'\
'U3EjMXagL2Wn7N4dEOTlvu6VU7F5fxSdB+WqOD623iJKzFpVkZMXcc2HjZcF'\
'iRKJBe+MMucdHo8T/ysdd8E2PwB7j7p0S+1GohHsRnkK0cGVL3y0zQ78Nl9j'\
'/fnspmESPMKhuXsh/+mQqUfuR2ZxXB7Wi+pkPqdzaPJE6gu8FcPiuDpZVHJi'\
'zL/VbUv5'
therevolution = zlib.decompress(base64.b64decode(therevolution))
header = '<b>Dec 19th, cableleaksweap day</b><br>Get a <a '\
'href="http://github.com/jesse-b-semple/the_revolution_will_be_live">'\
'copy of this code</a> and upload the cablegate files to a blog of your'\
'choice on that day<br><br>'

def get_url(url):
	opener = urllib.urlopen(url, data=None, proxies=proxy)
	data = opener.read()
	encoding = opener.headers.get('content-encoding',0)
	opener.close()
	if encoding == "gzip":
		bytestream = io.BytesIO(data)
		return gzip.GzipFile(fileobj=bytestream, mode="rb").read()
	else:
		return data

def check_proxy():
	print "Verifying proxy"
	print "IP without proxy:",
	print BeautifulSoup.BeautifulSoup(urllib.urlopen(
		'http://check.torproject.org/', 
		proxies=None).read()).find('b').string
	print "IP with proxy:",
	print  BeautifulSoup.BeautifulSoup(urllib.urlopen(
		'http://check.torproject.org/', 
		proxies=proxy).read()).find('b').string

def resolve_url(url, concaturl=None):
	""" concaturl used to keep within the url directory context of 
	    caller """
	if url[:7] in ('http://', 'HTTP://'):
		return url
	else:
		if concaturl:
			concat = urlparse.urljoin(cablegateurlroot, concaturl)
			return urlparse.urljoin(concat, re.sub('^/*\.\./', '', url))
		else:
			return urlparse.urljoin(cablegateurlroot, 
					re.sub('^/*\.\./', '', url))

def url_to_relative_path(url):
	path = urlparse.urlparse(url)[2]
	return re.sub('^(/\.\./|\.\./|/)/*', '', path) #bleh

def download_index_page_recursive(url, path):
	""" path relative, url absolute """
	if os.path.exists(path):
		print "%s: have index already, assuming we skip"%path
		return

	print "%s: getting index and storing locally"%path
	html = get_url(url)
	open(path, 'w').write(html)
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
	#html  = urllib.urlopen(cablegateurl, proxies=proxy)
	html  = get_url(cablegateurl)
	soup  = BeautifulSoup.BeautifulSoup(html)
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
			url  = resolve_url(url['href'])
			path = url_to_relative_path(url)
			if not os.path.exists(path):
				print "downloading cable: %s (%s)"%(path, url)
				html  = get_url(url)# urllib.urlopen(url, proxies=proxy).read()
				dir   = os.path.dirname(path)
				if not os.path.exists(dir):
					os.makedirs(dir)
				open(path, 'w').write(html)
			
# Parse upload cables
subject_re  = re.compile(".*(SUBJECT|Subject):\s*([^\n]*)", 
		re.MULTILINE | re.DOTALL)
ref_re      = re.compile(".*(REF|Ref):\s*([^\n]*)", 
		re.MULTILINE | re.DOTALL)
ref_re_simp = re.compile("REF:|Ref:", re.MULTILINE | re.DOTALL)
tags_re     = re.compile('TAGS:|Tags:')
tags2a_re   = re.compile('TAGS')
tags2b_re   = re.compile(".*TAGS\s+([^\n]*)", re.MULTILINE | re.DOTALL)
tags_link_re = re.compile('tag/')
def parse_and_upload_cable(path):
	html = open(path).read()
	html = re.sub('&#x000A;', "\n", html)
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
	post_cats = ['Cablegate']
	keywords = []
	keywords.append(tags)
	keywords.append(reference_id)
	keywords.append(origin)
	keywords.append(classification)
	keywords.append('cablegate')
	keywords.append('wikileaks')
	# make categories:
	for tag in tags:
		if not blog.suggest_categories(tag, blogid): 
			blog.new_category({'name': tag, 'slug':tag,
				'parent_id': cat_tag_id, 'description': ''})
		post_cats.append(tag)
	origin = origin.replace(' ', '_')
	if not blog.suggest_categories(origin, blogid):
		blog.new_category({'name': origin, 'slug':origin,
			'parent_id': cat_embassy_id, 'description': ''})
	post_cats.append(origin)
	classification = classification.replace('/', '_')
	if not blog.suggest_categories(classification, blogid):
		blog.new_category({'name': classification, 'slug':classification,
			'parent_id': cat_classification_id, 'description': ''})
	post_cats.append(classification)
	post = {
			'title': subject,
			'description': support+str(part1)+str(part2),
			'dateCreated': created_time,
			'categories': post_cats,
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

# Setup blog connection
title_to_ref_re = re.compile("^([^\:]+):")
refs_online = {}
def setup_blog():
	print "Connecting to blog"
	global blog, blogid
	try:
		if proxyurl:
			blog = pyblog.WordPress(blogrpcurl, user, password, 
					urlparse.urlparse(proxyurl)[1])
		else:
			blog = pyblog.WordPress(blogrpcurl, user, password)
	except Exception, err:
		print "Error connecting to blog. If using a proxy,"
		print "Try again or help us improve the code few."
		print
		print str(err)
		sys.exit(2)

def list_blogs():
	print "Blog ID's available:"
	i = 0
	setup_blog()
	for b in blog.get_users_blogs():
		print "%d: %s"%(i, b['blogName'])
		i += 1
	sys.exit(2)

def prep_blog():
	global cat_cablegate_id, cat_tag_id, cat_embassy_id, cat_classification_id
	# Upload code to blog page
	code = open(sys.argv[0]).read()
	code = code.replace('&', '&amp;')
	code = code.replace('<', '&lt;')
	code = code.replace('>', '&gt;')
	code = "<pre>"+code+"</pre>"

	html = header+therevolution+code
	page = {
		'title': "The Revolution Will Be Live",
		'wp_slug': "the_revolution_will_be_live",
		'description': html
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
	cat_cablegate          = {'name':'Cablegate', 'slug':'cablegate',
		                      'parent_id': 0, 'description': ''}
	cat_cablegate_id       = 0
	cat_tag                = {'name':'Tag', 'slug':'tag',
		                      'parent_id': 0, 'description': ''}
	cat_tag_id             = 0
	cat_embassy            = {'name':'Embassy', 'slug':'embassy',
		                      'parent_id': 0, 'description': ''}
	cat_embassy_id         = 0
	cat_classification     = {'name':'Classification', 'slug':'classification',
		                     'parent_id': 0, 'description': ''}
	cat_classification_id  = 0
	for c in cats:
		if c['description'] == cat_cablegate['name']:
			cat_cablegate_id      = c['categoryId']
		elif c['description'] == cat_tag['name']:
			cat_tag_id            = c['categoryId']
		elif c['description'] == cat_embassy['name']:
			cat_embassy_id        = c['categoryId']
		elif c['description'] == cat_classification['name']:
			cat_classification_id = c['categoryId']

	if not cat_cablegate_id:
		print "creating '%s' category"%cat_cablegate['name']
		blog.new_category(cat_cablegate, blogid)
	if not cat_embassy_id:
		print "creating '%s' category"%cat_embassy['name']
		cat_embassy_id = blog.new_category(cat_embassy, blogid)
	if not cat_classification_id:
		print "creating '%s' category"%cat_classification['name']
		cat_classification_id = blog.new_category(cat_classification, blogid)
	if not cat_tag_id:
		print "creating '%s' category"%cat_tag['name']
		cat_tag_id = blog.new_category(cat_tag, blogid)



def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hu:p:b:t:i:c:x:y", ["help"
			"user=", 'password=', 'blogrpc=', 'blogtype=', 'blogid=', 
			'cablegate=', 'proxy=',  'proxycheck'])
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
				cablegateurlroot='://'.join(urlparse.urlsplit(cablegateurl)[0:2])
		elif o in ("-x", "--proxy"):
			proxyurl = a
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
	prep_blog()
	upload_cables()

	


if __name__ == "__main__":
    main()
