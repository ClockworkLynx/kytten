# kytten/theme.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import os

import pyglet
from pyglet import gl

try:
    import json
    json_load = json.loads
except ImportError:
    try:
	import simplejson as json
	json_load = json.loads
    except ImportError:
	import sys
	print >>sys.stderr, \
	      "Warning: using 'safe_eval' to process json files, " \
	      "please upgrade to Python 2.6 or install simplejson"
	import safe_eval
	def json_load(expr):
	    # strip carriage returns
	    return safe_eval.safe_eval(''.join(str(expr).split('\r')))

DEFAULT_THEME_SETTINGS = {
    "font": "Lucida Grande",
    "font_size": 12,
    "font_size_small": 10,
    "text_color": [255, 255, 255, 255],
    "gui_color": [255, 255, 255, 255],
    "highlight_color": [255, 255, 255, 64],
    "disabled_color": [160, 160, 160, 255],
}

class ThemeTextureGroup(pyglet.graphics.TextureGroup):
    """
    ThemeTextureGroup, in addition to setting the texture, also ensures that
    we map to the nearest texel instead of trying to interpolate from nearby
    texels.  This prevents 'blooming' along the edges.
    """
    def set_state(self):
	pyglet.graphics.TextureGroup.set_state(self)
	gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
			   gl.GL_NEAREST)
	gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
			   gl.GL_NEAREST)

class UndefinedGraphicElementTemplate:
    def __init__(self, theme):
	self.theme = theme
	self.width = 0
	self.height = 0
	self.margins = [0, 0, 0, 0]
	self.padding = [0, 0, 0, 0]

    def generate(self, color, batch, group):
	return UndefinedGraphicElement(self.theme, color, batch, group)

    def write(self, f, indent=0):
        f.write('None')

class TextureGraphicElementTemplate(UndefinedGraphicElementTemplate):
    def __init__(self, theme, texture, width=None, height=None):
	UndefinedGraphicElementTemplate.__init__(self, theme)
	self.texture = texture
	self.width = width or texture.width
	self.height = height or texture.height

    def generate(self, color, batch, group):
	return TextureGraphicElement(self.theme, self.texture,
				     color, batch, group)

    def write(self, f, indent=0):
	f.write('{\n')
	f.write(' ' * (indent + 2) + '"src": "%s"' % self.texture.src)
	if hasattr(self.texture, 'region'):
	    f.write(',\n' + ' ' * (indent + 2) + '"region": %s' %
		    repr(list(self.texture.region)))
	f.write('\n' + ' ' * indent + '}')

class FrameTextureGraphicElementTemplate(TextureGraphicElementTemplate):
    def __init__(self, theme, texture, stretch, padding,
		 width=None, height=None):
	TextureGraphicElementTemplate.__init__(self, theme, texture,
					       width=width, height=height)
	self.stretch_texture = texture.get_region(*stretch).get_texture()
	x, y, width, height = stretch
	self.margins = (x, texture.width - width - x,   # left, right
			texture.height - height - y, y) # top, bottom
	self.padding = padding

    def generate(self, color, batch, group):
	return FrameTextureGraphicElement(
	    self.theme, self.texture, self.stretch_texture,
	    self.margins, self.padding, color, batch, group)

    def write(self, f, indent=0):
	f.write('{\n')
	f.write(' ' * (indent + 2) + '"src": "%s"' % self.texture.src)
	if hasattr(self.texture, 'region'):
	    f.write(',\n' + ' ' * (indent + 2) + '"region": %s' %
		    repr(list(self.texture.region)))
	left, right, top, bottom = self.margins
	if left != 0 or right != 0 or top != 0 or bottom != 0 or \
	   self.padding != [0, 0, 0, 0]:
	    stretch = [left, bottom,
		       self.width - right - left, self.height - top - bottom]
	    f.write(',\n' + ' ' * (indent + 2) + '"stretch": %s' %
		    repr(list(stretch)))
	    f.write(',\n' + ' ' * (indent + 2) + '"padding": %s' %
		    repr(list(self.padding)))
	f.write('\n' + ' ' * indent + '}')

class TextureGraphicElement:
    def __init__(self, theme, texture, color, batch, group):
	self.x = self.y = 0
	self.width, self.height = texture.width, texture.height
	self.group = ThemeTextureGroup(texture, group)
	self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
				     ('v2i', self._get_vertices()),
				     ('c4B', color * 4),
				     ('t3f', texture.tex_coords))

    def _get_vertices(self):
	x1, y1 = int(self.x), int(self.y)
	x2, y2 = x1 + int(self.width), y1 + int(self.height)
	return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
	self.vertex_list.delete()
	self.vertex_list = None
	self.group = None

    def get_content_region(self):
	return (self.x, self.y, self.width, self.height)

    def get_content_size(self, width, height):
	return width, height

    def get_needed_size(self, content_width, content_height):
	return content_width, content_height

    def update(self, x, y, width, height):
	self.x, self.y, self.width, self.height = x, y, width, height
	if self.vertex_list is not None:
	    self.vertex_list.vertices = self._get_vertices()

class FrameTextureGraphicElement:
    def __init__(self, theme, texture, inner_texture, margins, padding,
		 color, batch, group):
	self.x = self.y = 0
	self.width, self.height = texture.width, texture.height
	self.group = ThemeTextureGroup(texture, group)
	self.outer_texture = texture
	self.inner_texture = inner_texture
	self.margins = margins
	self.padding = padding
	self.vertex_list = batch.add(36, gl.GL_QUADS, self.group,
				     ('v2i', self._get_vertices()),
				     ('c4B', color * 36),
				     ('t2f', self._get_tex_coords()))

    def _get_tex_coords(self):
        x1, y1 = self.outer_texture.tex_coords[0:2] # outer's lower left
        x4, y4 = self.outer_texture.tex_coords[6:8] # outer's upper right
        x2, y2 = self.inner_texture.tex_coords[0:2] # inner's lower left
        x3, y3 = self.inner_texture.tex_coords[6:8] # inner's upper right
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def _get_vertices(self):
        left, right, top, bottom = self.margins
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(left), y1 + int(bottom)
        x3 = x1 + int(self.width) - int(right)
	y3 = y1 + int(self.height) - int(top)
        x4, y4 = x1 + int(self.width), y1 + int(self.height)
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def get_content_region(self):
	left, right, top, bottom = self.padding
	return (self.x + left, self.y + bottom,
		self.width - left - right, self.height - top - bottom)

    def get_content_size(self, width, height):
	left, right, top, bottom = self.padding
	return width - left - right, height - top - bottom

    def get_needed_size(self, content_width, content_height):
	left, right, top, bottom = self.padding
	return (max(content_width + left + right, self.outer_texture.width),
	        max(content_height + top + bottom, self.outer_texture.height))

    def delete(self):
	self.vertex_list.delete()
	self.vertex_list = None
	self.group = None

    def update(self, x, y, width, height):
	self.x, self.y, self.width, self.height = x, y, width, height
	if self.vertex_list is not None:
	    self.vertex_list.vertices = self._get_vertices()

class UndefinedGraphicElement(TextureGraphicElement):
    def __init__(self, theme, color, batch, group):
	self.x = self.y = self.width = self.height = 0
	self.group = group
	self.vertex_list = batch.add(12, gl.GL_LINES, self.group,
				     ('v2i', self._get_vertices()),
				     ('c4B', color * 12))

    def _get_vertices(self):
	x1, y1 = int(self.x), int(self.y)
	x2, y2 = x1 + int(self.width), y1 + int(self.height)
	return (x1, y1, x2, y1, x2, y1, x2, y2,
		x2, y2, x1, y2, x1, y2, x1, y1,
		x1, y1, x2, y2, x1, y2, x2, y1)

class ScopedDict(dict):
    """
    ScopedDicts differ in several useful ways from normal dictionaries.

    First, they are 'scoped' - if a key exists in a parent ScopedDict but
    not in the child ScopedDict, we return the parent value when asked for it.

    Second, we can use paths for keys, so we could do this:
        path = ['button', 'down', 'highlight']
	color = theme[path]['highlight_color']

    This would return the highlight color assigned to the highlight a button
    should have when it is clicked.
    """
    def __init__(self, arg={}, parent=None):
	self.parent = parent
	for k, v in arg.iteritems():
	    if isinstance(v, dict):
		self[k] = ScopedDict(v, self)
	    else:
		self[k] = v

    def __getitem__(self, key):
	if key is None:
	    return self
	elif isinstance(key, list) or isinstance(key, tuple):
	    if len(key) > 1:
		return self.__getitem__(key[0]).__getitem__(key[1:])
	    elif len(key) == 1:
		return self.__getitem__(key[0])
	    else:
		return self  # theme[][key] should return theme[key]
	else:
	    try:
		return dict.__getitem__(self, key)
	    except KeyError:
		if self.parent is not None:
		    return self.parent.__getitem__(key)
		else:
		    raise

    def __setitem__(self, key, value):
	if isinstance(value, dict):
	    dict.__setitem__(self, key, ScopedDict(value, self))
	else:
	    dict.__setitem__(self, key, value)

    def get(self, key, default=None):
	if isinstance(key, list) or isinstance(key, tuple):
	    if len(key) > 1:
		return self.__getitem__(key[0]).get(key[1:], default)
	    elif len(key) == 1:
		return self.get(key[0], default)
	    else:
		raise KeyError(key)  # empty list

	if self.has_key(key):
	    return dict.get(self, key)
	elif self.parent:
	    return self.parent.get(key, default)
	else:
	    return default

    def get_path(self, path, default=None):
	assert isinstance(path, list) or isinstance(path, tuple)
	if len(path) == 1:
	    return self.get(path[0], default)
	else:
	    return self.__getitem__(path[0]).get_path(path[1:], default)

    def set_path(self, path, value):
	assert isinstance(path, list) or isinstance(path, tuple)
	if len(path) == 1:
	    return self.__setitem__(path[0], value)
	else:
	    return self.__getitem__(path[0]).set_path(path[1:], value)

    def write(self, f, indent=0):
	f.write('{\n')
	first = True
	for k, v in self.iteritems():
	    if not first:
		f.write(',\n')
	    else:
		first = False
	    f.write(' ' * (indent + 2) + '"%s": ' % k)
	    if isinstance(v, ScopedDict):
		v.write(f, indent + 2)
	    elif isinstance(v, UndefinedGraphicElementTemplate):
		v.write(f, indent + 2)
	    elif isinstance(v, basestring):
		f.write('"%s"' % v)
	    elif isinstance(v, tuple):
		f.write('%s' % repr(list(v)))
	    else:
		f.write(repr(v))
	f.write('\n')
	f.write(' ' * indent + '}')

class Theme(ScopedDict):
    """
    Theme is a dictionary-based class that converts any elements beginning
    with 'image' into a GraphicElementTemplate.  This allows us to specify
    both simple textures and 9-patch textures, and more complex elements.
    """
    def __init__(self, arg, override={}, default=DEFAULT_THEME_SETTINGS,
		 allow_empty_theme=False, name='theme.json'):
	"""
	Creates a new Theme.

	@param arg The initializer for Theme.  May be:
	    * another Theme - we'll use the same graphic library but
	                      apply an override for its dictionary.
	    * a dictionary - interpret any subdirectories where the key
			     begins with 'image' as a GraphicElementTemplate
	    * a filename - read the JSON file as a dictionary
	@param override Replace some dictionary entries with these
	@param default Initial dictionary entries before handling input
	@param allow_empty_theme True if we should allow creating a new theme
	"""
	ScopedDict.__init__(self, default, None)

	self.groups = {}

	if isinstance(arg, Theme):
	    self.textures = arg.textures
	    for k, v in arg.iteritems():
		self.__setitem__(k, v)
	    self.update(override)
	    return

	if isinstance(arg, dict):
	    self.loader = pyglet.resource.Loader(os.getcwd())
	    input = arg
	else:
	    if os.path.isfile(arg) or os.path.isdir(arg):
		self.loader = pyglet.resource.Loader(path=arg)
		try:
		    theme_file = self.loader.file(name)
		    input = json_load(theme_file.read())
		    theme_file.close()
		except pyglet.resource.ResourceNotFoundException:
		    input = {}
	    else:
		input = {}

	self.textures = {}
	self._update_with_images(self, input)
	self.update(override)

    def __getitem__(self, key):
	try:
	    return ScopedDict.__getitem__(self, key)
	except KeyError, e:
	    if key.startswith('image'):
		return UndefinedGraphicElementTemplate(self)
	    else:
		raise e

    def _get_texture(self, filename):
	"""
	Returns the texture associated with a filename.  Loads it from
	resources if we haven't previously fetched it.

	@param filename The filename of the texture
	"""
	if not self.textures.has_key(filename):
	    texture = self.loader.texture(filename)
	    texture.src = filename
	    self.textures[filename] = texture
	return self.textures[filename]

    def _get_texture_region(self, filename, x, y, width, height):
	"""
	Returns a texture region.

	@param filename The filename of the texture
	@param x X coordinate of lower left corner of region
	@param y Y coordinate of lower left corner of region
	@param width Width of region
	@param height Height of region
	"""
	texture = self._get_texture(filename)
	retval = texture.get_region(x, y, width, height).get_texture()
	retval.src = texture.src
	retval.region = [x, y, width, height]
	return retval

    def _update_with_images(self, target, input):
	"""
	Update a ScopedDict with the input dictionary.  Translate
	images into texture templates.

	@param target The ScopedDict which is to be populated
	@param input The input dictionary
	"""
	for k, v in input.iteritems():
	    if k.startswith('image'):
		if isinstance(v, dict):
		    width = height = None
		    if v.has_key('region'):
			x, y, width, height = v['region']
			texture = self._get_texture_region(
				v['src'], x, y, width, height)
		    else:
			texture = self._get_texture(v['src'])
		    if v.has_key('stretch'):
			target[k] = FrameTextureGraphicElementTemplate(
			    self,
			    texture,
			    v['stretch'],
			    v.get('padding', [0, 0, 0, 0]),
			width=width, height=height)
		    else:
			target[k] = TextureGraphicElementTemplate(
			    self, texture, width=width, height=height)
		else:
		    target[k] = TextureGraphicElementTemplate(
			self, self._get_texture(v))
	    elif isinstance(v, dict):
		temp = ScopedDict(parent=target)
		self._update_with_images(temp, v)
		target[k] = temp
	    else:
		target[k] = v

    def write(self, f, indent=0):
	ScopedDict.write(self, f, indent)
	f.write('\n')
