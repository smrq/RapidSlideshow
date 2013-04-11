#/usr/bin/env python

import os, argparse, glob, random, threading, pygame

def is_image(filename):
	filename = filename.lower()
	return filename[filename.rfind(".")+1:] in ["jpg", "jpeg", "png", "gif"]

def get_images_from_glob(pathname):
	return [f for f in glob.glob(pathname) if is_image(f)]

def get_images_from_dir(pathname):
	return [os.path.join(pathname, f) for f in os.listdir(pathname) if is_image(f)]

def get_image_from_filename(pathname):
	if is_image(pathname):
		return [pathname]
	return []

def pick_random_image(pathnames):
	images = []
	for pathname in pathnames:
		if '*' in pathname or '?' in pathname:
			images.extend(get_images_from_glob(pathname))
		elif os.path.isdir(pathname):
			images.extend(get_images_from_dir(pathname))
		elif os.path.isfile(pathname):
			images.extend(get_image_from_filename(pathname))
	return random.choice(images)

class SlideLoader:
	buffer = []
	bufferSize = 0
	lock = threading.Lock()
	loader = None

	def __init__(self, pathnames, bufferSize):
		self.loader = InfiniteLoopThread(lambda: self.load_random_slide(pathnames))
		self.bufferSize = bufferSize

	def start_loading(self):
		self.loader.start()

	def get_buffer_amount(self):
		return len(self.buffer) / self.bufferSize

	def load_random_slide(self, pathnames):
		filename = pick_random_image(pathnames)
		slide = pygame.image.load(open(filename, "rb")).convert()

		self.lock.acquire()
		self.buffer.append(slide)
		if len(self.buffer) > self.bufferSize:
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

def get_blit_position(surface, screen):
	surfaceWidth = surface.get_width()
	surfaceHeight = surface.get_height()
	screenWidth = screen.get_width()
	screenHeight= screen.get_height()
	return ((screenWidth - surfaceWidth)/2, (screenHeight - surfaceHeight)/2)

class Renderer(threading.Thread):
	daemon = True
	screen = None
	slideLoader = None
	fps = None
	minimumBufferFill = None

	def __init__(self, screen, slideLoader, fps, minimumBufferFill, showFps):
		threading.Thread.__init__(self)
		self.screen = screen
		self.slideLoader = slideLoader
		self.fps = fps
		self.minimumBufferFill = minimumBufferFill
		self.showFps = showFps

	def run(self):
		font = pygame.font.Font(None, 48)
		clock = pygame.time.Clock()
		backgroundColor = (0, 0, 0)
		textColor = (30, 30, 50)

		while 1:
			clock.tick(self.fps)
			self.screen.fill(backgroundColor)
			bufferAmount = self.slideLoader.get_buffer_amount()
			if bufferAmount < self.minimumBufferFill:
				text = 'Buffering... ({:.1%})'.format(bufferAmount / self.minimumBufferFill)
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, get_blit_position(textSurface, self.screen))
			else:
				slide = self.slideLoader.pick_random_slide()
				self.screen.fill(backgroundColor)
				self.screen.blit(slide, get_blit_position(slide, self.screen))
			if self.showFps:
				text = 'fps: {:.1f}'.format(clock.get_fps())
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, (10, 10))
			pygame.display.flip()

def main():
	parser = argparse.ArgumentParser(description='Display slides. Fast.')
	parser.add_argument('dir', help='Read images from DIR', nargs='+')
	parser.add_argument('-f', '--fps', help='Sets the framerate for displaying new slides', metavar='##', type=int, default=60)
	parser.add_argument('--buf', dest='bufferSize', help='Sets the size of the slide buffer', type=int, default=100, metavar='##')
	parser.add_argument('--fill', dest='minimumBufferFill', help='Sets the minimum buffer fill ratio before displaying begins', type=float, default=0.25, metavar='0.##')
	parser.add_argument('--debug', action='store_true')
	options = parser.parse_args()

	pygame.init()
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
	pygame.mouse.set_visible(0)

	slideLoader = SlideLoader(options.dir, options.bufferSize)
	slideLoader.start_loading()

	renderer = Renderer(screen, slideLoader, options.fps, options.minimumBufferFill, options.debug)
	renderer.start()

	clock = pygame.time.Clock()
	while 1:
		clock.tick(5)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				return

if __name__ == '__main__': main()