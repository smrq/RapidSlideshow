import pygame, random, threading

def _get_random_blit_position(surface, screen):
	xMin = screen.get_width() - surface.get_width()
	xMid = xMin / 2
	xMax = 0
	yMin = screen.get_height() - surface.get_height()
	yMid = yMin / 2
	yMax = 0
	return (random.choice([xMin, xMid, xMax]), random.choice([yMin, yMid, yMax]))

def _get_centered_blit_position(surface, screen):
	surfaceWidth = surface.get_width()
	surfaceHeight = surface.get_height()
	screenWidth = screen.get_width()
	screenHeight = screen.get_height()
	return ((screenWidth - surfaceWidth)/2, (screenHeight - surfaceHeight)/2)

class Renderer(threading.Thread):
	daemon = True

	def __init__(self, process, screen, slideLoader, fps, debug):
		threading.Thread.__init__(self)
		self.process = process
		self.screen = screen
		self.slideLoader = slideLoader
		self.fps = fps
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
			if bufferAmount < 1:
				text = 'Buffering... ({:.1%})'.format(bufferAmount)
				textSurface = font.render(text, 1, textColor)
				self.screen.blit(textSurface, _get_centered_blit_position(textSurface, self.screen))
			else:
				slide = self.slideLoader.pick_random_slide()
				self.screen.fill(backgroundColor)
				self.screen.blit(slide, _get_random_blit_position(slide, self.screen))

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