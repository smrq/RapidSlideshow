import os, requests, shutil, tempfile
try:
	from xml.etree import cElementTree as ElementTree
except ImportError:
	from xml.etree import ElementTree

def _get_post_list(tags, pageIndex):
	params = { 'page': 'dapi', 's': 'post', 'q': 'index', 'tags': ' '.join(tags) }
	req = requests.get('http://gelbooru.com/index.php', params=params)
	req.raise_for_status()
	return req.text

def _get_urls_from_posts(posts, highResolution):
	if highResolution:
		pathAttrib = 'file_url'
	else:
		pathAttrib = 'sample_url'
	return [post.attrib[pathAttrib] for post in posts.iter('post')]

def _get_file_urls(tags, pageIndex, highResolution):
	xml = _get_post_list(tags, pageIndex)
	posts = ElementTree.fromstring(xml)
	urls = _get_urls_from_posts(posts, highResolution)

	totalPosts = int(posts.attrib['count'])
	offset = int(posts.attrib['offset'])
	remainingPosts = totalPosts - offset - len(posts)

	return [urls, remainingPosts]

class ImageboardImageFinder():
	def __enter__(self):
		self.tempDir = tempfile.mkdtemp()
		return self

	def __exit__(self, type, value, traceback):
		shutil.rmtree(self.tempDir)

	def __init__(self, tags, highResolution):
		self.tags = tags
		self.highResolution = highResolution
		self.fileUrls = []
		self.currentPageIndex = 0
		self.filePaths = []
		self.currentFileIndex = 0
		self.allUrlsRetrieved = False

	def find_image(self):
		if len(self.fileUrls) > 0:
			return self.cache_next_image()
		if self.allUrlsRetrieved:
			return self.get_next_cached_image()

		self.load_more_urls()

		if len(self.fileUrls) > 0:
			return self.cache_next_image()
		return self.get_next_cached_image()

	def load_more_urls(self):
		[urls, remainingPosts] = _get_file_urls(self.tags, self.currentPageIndex, self.highResolution)
		for url in urls:
			self.fileUrls.append(url)
		self.currentPageIndex = self.currentPageIndex + 1
		if remainingPosts == 0 or len(urls) == 0:
			self.allUrlsRetrieved = True

	def cache_next_image(self):
		url = self.fileUrls.pop(0)
		req = requests.get(url)
		req.raise_for_status()
		with tempfile.NamedTemporaryFile(dir=self.tempDir, delete=False) as f:
			for chunk in req.iter_content():
				f.write(chunk)
			self.filePaths.append(f.name)
			return f.name

	def get_next_cached_image(self):
		filePath = self.filePaths[self.currentFileIndex]
		self.currentFileIndex = (self.currentFileIndex + 1) % len(self.currentFileIndex)
		return filePath
