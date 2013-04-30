#/usr/bin/env python

import argparse, os, psutil, pygame
from filesystem_image_finder import FilesystemImageFinder
from renderer import Renderer
from slide_loader import SlideLoader

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

	imageFinder = FilesystemImageFinder(options.dir)

	slideLoader = SlideLoader(process, screen, imageFinder, options.maxMemoryUsage)
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