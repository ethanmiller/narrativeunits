import BeautifulSoup, zipfile, urllib, re, time
from threading import Thread

class Reader:
	def __init__(self):
		self.offset = self.get_offset()
		self.words = []
		self.links = []
		self.proc_index()
		self.dl = Dler(self.get_file_url()) 
		self.dl.start() # run thread
		self.dl.join() # wait for it to finish this once
		self.current_file = self.dl.file_name
		self.proc_zip() # parse words
		self.dl = Dler(self.get_file_url()) 
		self.dl.start() # run thread again to queue up the next file
	
	def proc_index(self):
		ufile = urllib.urlopen(self.get_index_url())
		soup = BeautifulSoup.BeautifulSoup(ufile)
		lks = soup('a')
		if len(lks) == 0:
			raise IndexError, ufile.info()
		self.links = ['http://www.gutenberg.org%s' % x['href'] for x in lks]

	def proc_zip(self):
		f = zipfile.ZipFile(self.current_file)
		self.words = f.read(f.filelist[0].filename).split()[2000:] # get rid of 2000 words which are (roughly) the standard disclaimer
		f.close()

	def get_index_url(self):
		return "http://www.gutenberg.org/robot/harvest?offset=%s&filetypes[]=txt" % self.offset	

	def get_file_url(self):
		nxt = self.links.pop(0)
		if not nxt.endswith('zip'):
			# we've reached the end of this index page
			self.proc_index()
			nxt = self.links.pop(0)
		self.inc_offset()
		return nxt

	def get_offset(self):
		f = open('offset', 'r')
		ret = int(f.read())
		f.close()
		return ret

	def inc_offset(self):
		self.offset += 1
		f = open('offset', 'w')
		f.write(str(self.offset))
		f.close()

	def next(self):
		madness, ct = (100, 0)
		while not self.words:
			self.dl.join() # wait for it to finish
			self.current_file = self.dl.file_name
			self.proc_zip() # parse words
			self.dl = Dler(self.get_file_url()) # new instance
			self.dl.start() # run thread again to queue up the next file
			ct += 1
			if ct > madness:
				raise IndexError, "WTF?"
		return self.current_file, self.words.pop(0)

class Dler(Thread):
	def __init__(self, u):
		Thread.__init__(self)
		self.file_name = None
		self.set_url(u)
	
	def set_url(self, u):
		self.url = u
		self.file_name = 'zips/' + self.url.split('/')[-1]

	def run(self):
		urllib.urlretrieve(self.url, self.file_name)
