#/usr/bin/env python

import argparse, os, psutil, pygame
from filesystem_image_finder import FilesystemImageFinder
from imageboard_image_finder import ImageboardImageFinder
from renderer import Renderer
from slide_loader import SlideLoader

def main():
	parser = argparse.ArgumentParser(description='Display slides. Fast.')
	parser.add_argument('-f', '--fps', help='Sets the framerate for displaying new slides', metavar='##', type=int, default=60)
	parser.add_argument('-m', '--mem', dest='maxMemoryUsage', help='Sets the maximum memory usage, as a percentage of total memory', type=float, default=50, metavar='##')
	parser.add_argument('-b', '--buffer', dest='minimumBufferLength', help='Sets the minimum buffered image count before displaying begins', type=int, default=25, metavar='##')
	parser.add_argument('--debug', action='store_true')

	subparsers = parser.add_subparsers(title='Subcommands')

	parser_dir = subparsers.add_parser('dir')
	parser_dir.add_argument('dirs', help='Directory to read images from (supports glob-style wildcards)', nargs='+', metavar='DIR')
	parser_dir.set_defaults(func=start_filesystem_mode)

	parser_gel = subparsers.add_parser('gel')
	parser_gel.add_argument('tags', help='Tags to search for', nargs='+', metavar='TAG')
	parser_gel.add_argument('--hq', help='Download higher-quality images', action='store_true')
	parser_gel.set_defaults(func=start_gelbooru_mode)

	options = parser.parse_args()
	options.func(options)

def start_filesystem_mode(options):
	imageFinder = FilesystemImageFinder(options.dirs)
	start(options, imageFinder)

def start_gelbooru_mode(options):
	with ImageboardImageFinder(options.tags, options.hq) as imageFinder:
		start(options, imageFinder)

def start(options, imageFinder):
	pygame.init()
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
	if not options.debug:
		pygame.mouse.set_visible(0)

	process = psutil.Process(os.getpid())

	slideLoader = SlideLoader(process, screen, imageFinder, options.minimumBufferLength, options.maxMemoryUsage)
	slideLoader.start()

	renderer = Renderer(process, screen, slideLoader, options.fps, options.debug)
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