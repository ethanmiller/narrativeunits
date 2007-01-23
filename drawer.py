import os, pygame, time, sys
from threading import Thread

class Drawer:
	def __init__(self):
		# pygame window
		self.size = self.width, self.height = 1024, 768
		self.window = pygame.display.set_mode(self.size)

		# directories of images
		self.imgdirs = os.listdir('vseq')
		self.imgdirs = [x for x in self.imgdirs if not x.startswith('.')]
		self.idir = 0
		self.dir = self.imgdirs[0]
	
		# load first set of images
		self.loader = Vloader(self.dir, False)
		self.loader.start()
		self.loader.join() # wait for it on the first run
		self.pyimgs = self.loader.pyimgs
		
		# start loading next set of images
		self.scrolldirs()
		self.loader = Vloader(self.dir)
		self.loader.start()

		#timing 
		self.lastframe = time.time()
		self.baseinterval = 0.05
		self.cinterval = self.baseinterval
		self.lengthenby = 0.10

		# pygame
		pygame.init()
		self.bg = pygame.image.load('bg.png')
		self.window.blit(self.bg, (0, 0))
		# text
		self.narrfont = pygame.font.Font("Crisp.ttf", 14)
		self.narrborder = (10, 10, 1034, 758)
		self.narrpos = self.narrborder[:2]
		# definition
		self.cdefpanel, self.odefpanel = (None, None)
		# sounds
		auf = ['bell', 'seq0', 'seq2', 'seq4', 'seq6']
		self.audio = {}
		for f in auf:
			self.audio[f] = pygame.mixer.Sound('audio/%s.wav' % f)
		self.audio['bell'].set_volume(0.02)

	def scrolldirs(self):
		self.idir = (self.idir + 1) % len(self.imgdirs)
		self.dir = self.imgdirs[self.idir]

	def draw(self, src, term, defbit, narrbit, match=False, dspace=True, nspace=True):
		# watch for quit
		for e in pygame.event.get():
			if e.type == pygame.QUIT:
				sys.exit()
            		elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
				sys.exit()
			elif e.type == pygame.KEYDOWN and e.key == pygame.K_F10:
				pygame.display.toggle_fullscreen()
				pygame.mouse.set_visible(False)

		if match:
			c = (250, 30, 0)
			self.audio['bell'].play()
			# also reset interval for movie
			self.cinterval = self.baseinterval
		else:
			c = (250, 250, 250)
			l = len(narrbit)
			l = l - (l % 2)
			if l > 6: 
				l = 6
			self.audio['seq%s' % l].play()

		#add space if needed
		if nspace:
			narrbit += ' '

		# print the next narrative word/letter, and scroll the position for the next text/letter
    		narrtext = self.narrfont.render(narrbit, 0, c)
		# the scroll confirms narrpos will work, tells us if the screen will refresh, and 
		# gives us the next position
		rfresh, self.narrpos, nxtpos = scrolltext(narrtext, self.narrpos, self.narrborder)
		if rfresh:
			# reset the background
			self.window.blit(self.bg, (0, 0))
    		self.window.blit(narrtext, self.narrpos)
		self.narrpos = nxtpos


		#definition panels
		if not self.cdefpanel:
			self.cdefpanel = Defpanel(term)
		if term != self.cdefpanel.term:
			# time to scroll to the next
			self.odefpanel = self.cdefpanel
			self.cdefpanel = Defpanel(term)
		self.window.blit(self.cdefpanel.draw(match, defbit, dspace), self.cdefpanel.xy)
		if self.odefpanel:
			self.window.blit(self.odefpanel.draw(), self.odefpanel.xy)
			self.odefpanel.slide()

		# the film....................
		now = time.time()
		if rfresh or now - self.lastframe > self.cinterval:
			if rfresh:
				self.pyimgs[0].set_alpha(255)
			self.window.blit(self.pyimgs.pop(0), (192, 30))
			# lengthen time
			self.cinterval += self.lengthenby
			self.lastframe = now

		if len(self.pyimgs) == 0:
			# collect most recent image sequence, and start loading next one.
			self.loader.join()
			self.pyimgs = self.loader.pyimgs
			self.scrolldirs()
			self.loader = Vloader(self.dir)
			self.loader.start()
		
		# finally......
		pygame.display.flip()
			
class Defpanel:
	def __init__(self, term):
		self.term = term
		self.xy = (190, 512)
		self.pasty = 512
		self.border = (10, 10, 634, 114)
		self.font = pygame.font.Font("Crisp.ttf", 24)
		self.c = (250, 30, 0)
		self.pos = self.border[:2]
		# create a surface
		self.surf = pygame.Surface((644, 114))
		self.surf.fill((38, 38, 38))
		# start the text on the surface
		self.txt = self.font.render(term + ' : ', 0, self.c)
		self.pos, nxt = scrolltext(self.txt, self.pos, self.border)[1:]
		self.surf.blit(self.txt, self.pos)
		self.pos = nxt

	def draw(self, match=False, char=None, space=False):
		if match:
			if space:
				char += ' '
			self.txt = self.font.render(char, 0, self.c)
			self.pos, nxt = scrolltext(self.txt, self.pos, self.border)[1:]
			self.surf.blit(self.txt, self.pos)
			self.pos = nxt
		if self.pasty != self.xy[1]:
			self.surf.set_alpha(100)
		elif self.xy[1] != 512:
			self.surf.set_alpha(5)
		else:
			self.surf.set_alpha(10)
		return self.surf

	def slide(self):
		if self.xy[1] == 630:
			return
		diff = 630 - self.xy[1]
		if diff < 0.5:
			self.xy = (190, 630)
			self.pasty = 630
		else:
			self.pasty = self.xy[1]
			self.xy = (190, self.xy[1] + diff/5.0)

class Vloader(Thread):
	def __init__(self, dir, pausestep=True):
		Thread.__init__(self)
		self.path = 'vseq/' + dir
		self.pyimgs = []
		self.pauses = pausestep

	def run(self):
		imgs = os.listdir(self.path)
		imgs.sort()
		for x in imgs:
			if not x.startswith('.'):
				i = pygame.image.load('/'.join((self.path, x)))
				i.set_alpha(70)
				self.pyimgs.append(i)
				if self.pauses:
					time.sleep(0.2)
	
def scrolltext(txt, pos, border):
	''' Takes a "proposed" pos for the given txt, and the limits within which the text should fit.
	Returns the final pos for the text, a bool to determine if the screen should be refreshed (i.e. when the 
	narrative text reaches the bottom of the screen), and the "proposal" for the next text position'''
	refreshscreen = False
	tsz = txt.get_size()
	propx, propy = pos[:2]
	nextx, nexty = (propx + tsz[0], propy)
	if nextx > border[2]:
		propx, propy = (border[0], propy + tsz[1])
		nextx, nexty = (propx + tsz[0], propy)
		if propy > border[3]:
			propx, propy = border[:2]
			nextx, nexty = (propx + tsz[0], propy)
			refreshscreen = True
	return refreshscreen, (propx, propy), (nextx, nexty)
