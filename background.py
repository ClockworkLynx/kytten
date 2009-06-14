# background.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import glob
import os
import pyglet
from pyglet import gl

class Background:
    """Selects one of several backgrounds to display behind the test dialog."""

    def __init__(self, loc=os.getcwd(), batch=None, group=None):
	"""
	Load a set of backgrounds from a given directory.

	@param loc  Location, defaults to current working directory.
	@param batch Batch to which to add our background
	@param group Group to which to add our background
	"""
	filenames = glob.glob(os.path.join(loc, '*.jpg'))
	images = [pyglet.image.load(x) for x in filenames]
	self.textures = [x.get_texture() for x in images]
	self.texture = None
	self.vertex_list = None
	if batch is None:
	    self.batch = pyglet.graphics.Batch()
	    self.own_batch = True
	else:
	    self.own_batch = False
	    self.batch = batch
	self.parent_group = group
	self.group = None
	self.width = self.height = 0
	self.needs_resizing = False

    def draw(self):
	if self.own_batch:
	    self.batch.draw()
	else:
	    self.batch.draw_subset([self.vertex_list])

    def on_key_press(self, symbol, modifiers):
	next_texture = None
	if symbol == pyglet.window.key.RIGHT:
	    next_texture = self.textures.pop(0)
	    if self.texture is not None:
		self.textures.append(self.texture)
	elif symbol == pyglet.window.key.LEFT:
	    next_texture = self.textures.pop(-1)
	    if self.texture is not None:
		self.textures.insert(0, self.texture)
	if next_texture is not None:
	    self.texture = next_texture
	    self.needs_resizing = True
	    return pyglet.event.EVENT_HANDLED

    def on_resize(self, width, height):
	if width != self.width or height != self.height:
	    self.width, self.height = width, height
	    self.needs_resizing = True

    def on_update(self, dt):
	# We only update the background size on on_update because
	# otherwise we might receive several resize events between frames.
	if not self.needs_resizing:
	    return
	self.needs_resizing = False

	if self.texture is None:
	    self.texture = self.textures.pop(0) # pick first texture

	if self.vertex_list is not None:
	    self.vertex_list.delete() # clear existing vertex_list

	# Now size the texture quad to retain its proportions but completely
	# overlap the screen
	our_width = self.texture.width * self.height / self.texture.height
	if our_width >= self.width:
	    our_height = self.height
	else:
	    our_height = self.texture.height * self.width / self.texture.width
	    our_width = self.width
	x1 = int(self.width/2 - our_width/2)
	y1 = int(self.height/2 - our_height/2)
	x2, y2 = x1 + our_width, y1 + our_height
	self.group = pyglet.graphics.TextureGroup(
	    self.texture, self.parent_group)
	self.vertex_list = self.batch.add(4, gl.GL_QUADS, self.group,
	    ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
	    ('c3B', (255, 255, 255) * 4),
	    ('t3f', self.texture.tex_coords))

