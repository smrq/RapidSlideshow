import glob, os, random

def _is_image(filename):
	filename = filename.lower()
	return filename[filename.rfind(".")+1:] in ['jpg', 'jpeg', 'png', 'gif']

def _get_images_from_glob(pathname):
	return [f for f in glob.glob(pathname) if _is_image(f)]

def _get_images_from_dir(pathname):
	return [os.path.join(pathname, f) for f in os.listdir(pathname) if _is_image(f)]

def _get_image_from_filename(pathname):
	if _is_image(pathname):
		return [pathname]
	return []

class FilesystemImageFinder():
	def __init__(self, pathnames):
		self.images = []
		for pathname in pathnames:
			if '*' in pathname or '?' in pathname:
				self.images.extend(_get_images_from_glob(pathname))
			elif os.path.isdir(pathname):
				self.images.extend(_get_images_from_dir(pathname))
			elif os.path.isfile(pathname):
				self.images.extend(_get_image_from_filename(pathname))

	def find_image(self):
		return random.choice(self.images)
