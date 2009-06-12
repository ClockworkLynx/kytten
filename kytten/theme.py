# kytten/theme.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

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
    "highlight_color": [255, 255, 255, 128],
}

class TextureGraphicElementTemplate:
    def __init__(self, texture, width=None, height=None):
	self.width = width or texture.width
	self.height = height or texture.height
	self.texture = texture

    def generate(self, color, batch, group):
	return TextureGraphicElement(self.texture, color, batch, group)

class FrameTextureGraphicElementTemplate:
    def __init__(self, texture, stretch, padding, width=None, height=None):
	self.width = width or texture.width
	self.height = height or texture.height
	self.texture = texture
	self.stretch_texture = texture.get_region(*stretch).get_texture()
	x, y, width, height = stretch
	self.margins = (x, texture.width - width - x,   # left, right
			texture.height - height - y, y) # top, bottom
	self.padding = padding

    def generate(self, color, batch, group):
	return FrameTextureGraphicElement(self.texture, self.stretch_texture,
					  self.margins, self.padding,
					  color, batch, group)

class TextureGroup(pyglet.graphics.TextureGroup):
    """
    TextureGroup, in addition to setting the texture, also ensures that
    we map to the nearest texel instead of trying to interpolate from nearby
    texels.  This prevents 'blooming' along the edges.
    """
    def set_state(self):
	pyglet.graphics.TextureGroup.set_state(self)
	gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
			   gl.GL_NEAREST)
	gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
			   gl.GL_NEAREST)

class TextureGraphicElement:
    def __init__(self, texture, color, batch, group):
	self.x = self.y = 0
	self.width, self.height = texture.width, texture.height
	self.group = TextureGroup(texture, group)
	self.vertex_list = batch.add(4, gl.GL_QUADS, self.group,
				     ('v2i', self._get_vertices()),
				     ('c4B', color * 4),
				     ('t3f', texture.tex_coords))

    def _get_vertices(self):
	x1, y1 = self.x, self.y
	x2, y2 = x1 + self.width, y1 + self.height
	return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
	self.vertex_list.delete()
	self.vertex_list = None

    def update(self, x, y, width, height):
	self.x, self.y, self.width, self.height = x, y, width, height
	if self.vertex_list is not None:
	    self.vertex_list.vertices = self._get_vertices()

class FrameTextureGraphicElement:
    def __init__(self, texture, inner_texture, margins, padding,
		 color, batch, group):
	self.x = self.y = 0
	self.width, self.height = texture.width, texture.height
	self.group = TextureGroup(texture, group)
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
        x1, y1 = self.x, self.y
        x2, y2 = x1 + left, y1 + bottom
        x3, y3 = x1 + self.width - right, y1 + self.height - top
        x4, y4 = x1 + self.width, y1 + self.height
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

    def update(self, x, y, width, height):
	self.x, self.y, self.width, self.height = x, y, width, height
	if self.vertex_list is not None:
	    self.vertex_list.vertices = self._get_vertices()

class ScopedDict(dict):
    def __init__(self, arg={}, parent=None):
	self.parent = parent
	for k, v in arg.iteritems():
	    if isinstance(v, dict):
		self[k] = ScopedDict(v, self)
	    else:
		self[k] = v

    def get(self, key, default=None):
	if self.has_key(key):
	    return dict.get(self, key)
	elif self.parent:
	    return self.parent.get(key, default)
	else:
	    return default

    def __getitem__(self, key):
	if key is None:
	    return self
	elif self.has_key(key):
	    return dict.__getitem__(self, key)
	elif self.parent:
	    return self.parent.__getitem__(key)
	else:
	    raise KeyError(key)

    def __setitem__(self, key, value):
	if isinstance(value, dict):
	    dict.__setitem__(self, key, ScopedDict(value, self))
	else:
	    dict.__setitem__(self, key, value)

class Theme(ScopedDict):
    """
    Theme is a dictionary-based class that converts any elements beginning
    with 'image' into a GraphicElementTemplate.  This allows us to specify
    both simple textures and 9-patch textures, and more complex elements.
    """
    def __init__(self, arg, override={}, default=DEFAULT_THEME_SETTINGS):
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
	"""
	ScopedDict.__init__(self, default, None)

	if isinstance(arg, Theme):
	    self.textures = arg.textures
	    for k, v in arg.iteritems():
		self.__setitem__(k, v)
	    self.update(override)
	    return

	if isinstance(arg, dict):
	    input = arg
	else:
	    loader = pyglet.resource.Loader(path=arg)
	    theme_file = loader.file('theme.json')
	    input = json_load(theme_file.read())
	    theme_file.close()

	self.textures = {}

	for k, v in input.iteritems():
	    if isinstance(v, dict):
		temp = ScopedDict(parent=self)
		for k2, v2 in v.iteritems():
		    if k2.startswith('image'):
			if isinstance(v2, dict):
			    width = height = None
			    if v2.has_key('region'):
				x, y, width, height = v2['region']
				texture = self._get_texture_region(
					v2['src'], x, y, width, height)
			    else:
				texture = self._get_texture(v2['src'])
			    if v2.has_key('stretch'):
				temp[k2] = FrameTextureGraphicElementTemplate(
				    texture,
				    v2['stretch'],
				    v2.get('padding', v2['stretch']),
				width=width, height=height)
			    else:
				temp[k2] = TextureGraphicElementTemplate(
				    texture, width=width, height=height)
			else:
			    temp[k2] = TextureGraphicElementTemplate(
				self._get_texture(v2))
		    else:
			temp[k2] = v2
		self[k] = temp
	    else:
		self[k] = v
	self.update(override)

    def _get_texture(self, filename):
	"""
	Returns the texture associated with a filename.  Loads it from
	resources if we haven't previously fetched it.

	@param filename The filename of the texture
	"""
	if not self.textures.has_key(filename):
	    self.textures[filename] = pyglet.resource.image(filename)
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
	return texture.get_region(x, y, width, height).get_texture()