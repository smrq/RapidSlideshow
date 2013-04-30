import math, pygame, random, threading

def _scale_surface_to_fit_width(surface, screen):
	scaleFactor = screen.get_width() / surface.get_width()
	return pygame.transform.scale(surface, (math.ceil(surface.get_width() * scaleFactor), math.ceil(surface.get_height() * scaleFactor)))

def _scale_surface_to_fit_height(surface, screen):
	scaleFactor = screen.get_height() / surface.get_height()
	return pygame.transform.scale(surface, (math.ceil(surface.get_width() * scaleFactor), math.ceil(surface.get_height() * scaleFactor)))

def _scale_surface_to_fit(surface, screen):
	screenAspectRatio = screen.get_width() / screen.get_height()
	surfaceAspectRatio = surface.get_width() / surface.get_height()
	if screenAspectRatio > surfaceAspectRatio:
		return _scale_surface_to_fit_height(surface, screen)
	else:
		return _scale_surface_to_fit_width(surface, screen)

def _scale_surface_to_fill(surface, screen):
	screenAspectRatio = screen.get_width() / screen.get_height()
	surfaceAspectRatio = surface.get_width() / surface.get_height()
	if screenAspectRatio < surfaceAspectRatio:
		return _scale_surface_to_fit_height(surface, screen)
	else:
		return _scale_surface_to_fit_width(surface, screen)

class SlideLoader(threading.Thread):
	daemon = True

	def __init__(self, process, screen, imageFinder, minimumBufferFilledLength, maxMemoryUsage):
		threading.Thread.__init__(self)
		self.process = process
		self.screen = screen
		self.imageFinder = imageFinder
		self.minimumBufferFilledLength = minimumBufferFilledLength
		self.maxMemoryUsage = maxMemoryUsage

		self.buffer = []
		self.lock = threading.Lock()

	def run(self):
		while 1:
			filename = self.imageFinder.find_image()
			slide = pygame.image.load(open(filename, "rb")).convert()
			scaledSlide = _scale_surface_to_fill(slide, self.screen)

			self.lock.acquire()

			self.buffer.append(scaledSlide)
			if self.process.get_memory_percent() > self.maxMemoryUsage:
				self.buffer.pop(0)

			self.lock.release()

	def get_buffer_amount(self):
		if self.process.get_memory_percent() >= self.maxMemoryUsage:
			return 1

		self.lock.acquire()
		bufferLength = len(self.buffer)
		self.lock.release()

		if bufferLength >= self.minimumBufferFilledLength:
			return 1

		return bufferLength / self.minimumBufferFilledLength

	def pick_random_slide(self):
		self.lock.acquire()
		slide = random.choice(self.buffer)
		self.lock.release()
		return slide
