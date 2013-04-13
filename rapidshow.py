#/usr/bin/env python

import os, argparse, glob, random, threading, math, pygame, psutil

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

def scale_surface_to_fit_width(surface, screen):
	scaleFactor = screen.get_width() / surface.get_width()
	return pygame.transform.scale(surface, (math.ceil(surface.get_width() * scaleFactor), math.ceil(surface.get_height() * scaleFactor)))

def scale_surface_to_fit_height(surface, screen):
	scaleFactor = screen.get_height() / surface.get_height()
	return pygame.transform.scale(surface, (math.ceil(surface.get_width() * scaleFactor), math.ceil(surface.get_height() * scaleFactor)))

def scale_surface_to_fit(surface, screen):
	screenAspectRatio = screen.get_width() / screen.get_height()
	surfaceAspectRatio = surface.get_width() / surface.get_height()
	if screenAspectRatio > surfaceAspectRatio:
		return scale_surface_to_fit_height(surface, screen)
	else:
		return scale_surface_to_fit_width(surface, screen)

def scale_surface_to_fill(surface, screen):
	screenAspectRatio = screen.get_width() / screen.get_height()
	surfaceAspectRatio = surface.get_width() / surface.get_height()
	if screenAspectRatio < surfaceAspectRatio:
		return scale_surface_to_fit_height(surface, screen)
	else:
		return scale_surface_to_fit_width(surface, screen)

class SlideLoader(threading.Thread):
	daemon = True

	def __init__(self, process, screen, pathnames, maxMemoryUsage):
		threading.Thread.__init__(self)
		self.process = process
		self.screen = screen
		self.pathnames = pathnames
		self.maxMemoryUsage = maxMemoryUsage

		self.buffer = []
		self.lock = threading.Lock()

	def run(self):
		while 1:
			filename = pick_random_image(self.pathnames)
			slide = pygame.image.load(open(filename, "rb")).convert()
			scaledSlide = scale_surface_to_fill(slide, self.screen)

			self.lock.acquire()

			self.buffer.append(scaledSlide)
			if self.process.get_memory_percent() > self.maxMemoryUsage:
				self.buffer.pop(0)

			self.lock.release()

	def get_buffer_amount(self):
		return self.process.get_memory_percent() / self.maxMemoryUsage

	def pick_random_slide(self):
		self.lock.acquire()
		slide = random.choice(self.buffer)
		self.lock.release()
		return slide

def get_centered_blit_position(surface, screen):
	surfaceWidth = surface.get_width()
	surfaceHeight = surface.get_height()
	screenWidth = screen.get_width()
	screenHeight = screen.get_height()
	return ((screenWidth - surfaceWidth)/2, (screenHeight - surfaceHeight)/2)

class Renderer(threading.Thread):
	daemon = True

	def __init__(self, process, screen, slideLoader, fps, minimumBufferAmount, debug):
		threading.Thread.__init__(self)
		self.process = process
		self.screen = screen
		self.slideLoader = slideLoader
		self.fps = fps
		self.minimumBufferAmount = minimumBufferAmount
		self.debug = debug

	def run(self):
		font = pygame.font.Font(None, 48)
		clock = pygame.time.Clock()
		backgroundColor = (0, 0, 0)
		textColor = (30, 30, 50)

		while 1:
			clock.tick(self.fps)
			self.screen.fill(backgroundColor)
			bufferAmount = self.slideLoader.get_buffer_amount()
			if bufferAmount < self.minimumBufferAmount:
				text = 'Buffering... ({:.1%})'.format(bufferAmount / self.minimumBufferAmount)
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, get_centered_blit_position(textSurface, self.screen))
			else:
				slide = self.slideLoader.pick_random_slide()
				self.screen.fill(backgroundColor)
				self.screen.blit(slide, get_centered_blit_position(slide, self.screen))

			if self.debug:
				# fps
				text = 'fps: {:.1f}'.format(clock.get_fps())
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, (10, 10))
				# resource usage
				text = 'memory: {:.1f}%'.format(self.process.get_memory_percent())
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, (10, 40))
				# buffer stats
				text = 'buffer: {:.1%}'.format(bufferAmount)
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, (10, 70))
			pygame.display.flip()

def main():
	parser = argparse.ArgumentParser(description='Display slides. Fast.')
	parser.add_argument('dir', help='Read images from DIR', nargs='+')
	parser.add_argument('-f', '--fps', help='Sets the framerate for displaying new slides', metavar='##', type=int, default=60)
	parser.add_argument('--mem', dest='maxMemoryUsage', help='Sets the maximum memory usage, as a percentage of total memory', type=float, default=50, metavar='##')
	parser.add_argument('--fill', dest='minimumBufferAmount', help='Sets the minimum buffer fill ratio before displaying begins', type=float, default=0.8, metavar='0.##')
	parser.add_argument('--debug', action='store_true')
	options = parser.parse_args()

	pygame.init()
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
	if not options.debug:
		pygame.mouse.set_visible(0)

	process = psutil.Process(os.getpid())

	slideLoader = SlideLoader(process, screen, options.dir, options.maxMemoryUsage)
	slideLoader.start()

	renderer = Renderer(process, screen, slideLoader, options.fps, options.minimumBufferAmount, options.debug)
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