#/usr/bin/env python

import os, argparse, random, threading, pygame

def is_image(filename):
	filename = filename.lower()
	return filename[filename.rfind(".")+1:] in ["jpg", "jpeg", "png", "gif"]

def pick_random_image(dirs):
	images = [os.path.join(dir, f) for dir in dirs for f in os.listdir(dir) if is_image(f)]
	return random.choice(images)

def get_blit_position(surface, screen):
	surfaceWidth = surface.get_width()
	surfaceHeight = surface.get_height()
	screenWidth = screen.get_width()
	screenHeight= screen.get_height()
	return ((screenWidth - surfaceWidth)/2, (screenHeight - surfaceHeight)/2)

class Slides:
	buffer = []
	bufferLength = 0
	lock = threading.Lock()
	loader = None

	def __init__(self, dirs, bufferLength):
		self.loader = InfiniteLoopThread(lambda: self.load_random_slide(dirs))
		self.bufferLength = bufferLength

	def start_loading(self):
		self.loader.start()

	def is_buffer_primed(self):
		return len(self.buffer) > min(3, self.bufferLength)

	def load_random_slide(self, dirs):
		filename = pick_random_image(dirs)
		slide = pygame.image.load(filename).convert()

		self.lock.acquire()
		self.buffer.append(slide)
		if len(self.buffer) > self.bufferLength:
			self.buffer.pop(0)
		self.lock.release()

	def pick_random_slide(self):
		self.lock.acquire()
		slide = random.choice(self.buffer)
		self.lock.release()
		return slide

class InfiniteLoopThread(threading.Thread):
	daemon = True
	fn = None
	def __init__(self, fn):
		threading.Thread.__init__(self)
		self.fn = fn
	def run(self):
		while 1:
			self.fn()

def run(dirs, fps, backgroundColor, bufferLength):
	pygame.init()
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
	pygame.mouse.set_visible(0)
	clock = pygame.time.Clock()

	slides = Slides(dirs, bufferLength)
	slides.start_loading()
	while not slides.is_buffer_primed():
		clock.tick(20)

	while 1:
		clock.tick(fps)
		slide = slides.pick_random_slide()
		screen.fill(backgroundColor)
		screen.blit(slide, get_blit_position(slide, screen))
		pygame.display.flip()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return

def main():
	parser = argparse.ArgumentParser(description='Display slides. Fast.')
	parser.add_argument('dir', help='Read images from DIR', nargs='+')
	parser.add_argument('-f', '--fps', help='Sets the framerate for displaying new slides', metavar='##', type=int, default=60)
	parser.add_argument('--buf', dest='bufferSize', help='Sets the size of the slide buffer', type=int, default=100, metavar='##')

	options = parser.parse_args()

	backgroundColor = (0, 0, 0)
	run(options.dir, options.fps, backgroundColor, options.bufferSize)

if __name__ == '__main__': main()