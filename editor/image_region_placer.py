# image_region_placer.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

import kytten
from kytten.widgets import Control

class ImageRegionPlacer(Control):
    """
    Display an image and a region within the image, which can be
    resized or moved.
    """
    IMAGE_REGION_COLOR = (255, 128, 64, 255)
    IMAGE_STRETCH_COLOR = (64, 255, 128, 255)
    IMAGE_PADDING_COLOR = (64, 128, 255, 255)

    def __init__(self, texture, x=0, y=0, width=0, height=0, scale=1,
		 on_resize=None):
	Control.__init__(self)
	self.texture = texture
	self.on_resize = on_resize
	self.texture_group = None
	self.texture_vlist = None
	self.resizer_vlist = None
	self.limits_vlist = None
	self.region = [x, y, width, height]
	self.limits = None
	self.scale = scale
	self.color = self.IMAGE_REGION_COLOR
	self.is_dragging = False
	self.corner = None

    def _get_controls(self):
	_, _, width, height = self.region
	if width < 20 or height < 20:
	    return [(self, self.x - 8, self.x + self.width + 8,
		           self.y + self.height + 8, self.y - 8)]
	else:
	    return Control._get_controls(self)

    def _get_limits_vertices(self):
	if self.limits is not None:
	    x, y, width, height = self.limits
	    x0 = int(self.x + x * self.scale)
	    y0 = int(self.y + y * self.scale)
	    x1 = x0 + int(width * self.scale)
	    y1 = y0 + int(height * self.scale)
	else:
	    x0, y0 = int(self.x), int(self.y)
	    x1 = x0 + int(self.width)
	    y1 = y0 + int(self.height)
	return [x0, y0, x1, y0, x1, y0, x1, y1,
		x1, y1, x0, y1, x0, y1, x0, y0]

    def _get_resizer_vertices(self):
	x, y, width, height = self.region
	if width < 20 or height < 20:  # sizer corners on outside
	    x0 = int(self.x + x * self.scale - 8)
	    y0 = int(self.y + y * self.scale - 8)
	    x1, y1 = x0 + 8, y0 + 8
	    x2 = x1 + int(width * self.scale)
	    y2 = y1 + int(height * self.scale)
	    x3, y3 = x2 + 8, y2 + 8
	    return [x1, y1, x2, y1, x2, y1, x2, y2, # center square
		    x2, y2, x1, y2, x1, y2, x1, y1,
		    x0, y0, x1, y0, x1, y0, x1, y1, # lower left
		    x1, y1, x0, y1, x0, y1, x0, y0,
		    x2, y0, x3, y0, x3, y0, x3, y1, # lower right
		    x3, y1, x2, y1, x2, y1, x2, y0,
		    x2, y2, x3, y2, x3, y2, x3, y3, # upper right
		    x3, y3, x2, y3, x2, y3, x2, y2,
		    x0, y2, x1, y2, x1, y2, x1, y3, # upper left
		    x1, y3, x0, y3, x0, y3, x0, y2]
	else:                          # sizer corners on inside
	    x0 = int(self.x + x * self.scale)
	    y0 = int(self.y + y * self.scale)
	    x1, y1 = x0 + 8, y0 + 8
	    x3 = x0 + int(width * self.scale)
	    y3 = y0 + int(height * self.scale)
	    x2, y2 = x3 - 8, y3 - 8
	    return [x0, y0, x3, y0, x3, y0, x3, y3, # center square
		    x3, y3, x0, y3, x0, y3, x0, y0,
		    x0, y0, x1, y0, x1, y0, x1, y1, # lower left
		    x1, y1, x0, y1, x0, y1, x0, y0,
		    x2, y0, x3, y0, x3, y0, x3, y1, # lower right
		    x3, y1, x2, y1, x2, y1, x2, y0,
		    x2, y2, x3, y2, x3, y2, x3, y3, # upper right
		    x3, y3, x2, y3, x2, y3, x2, y2,
		    x0, y2, x1, y2, x1, y2, x1, y3, # upper left
		    x1, y3, x0, y3, x0, y3, x0, y2]

    def _get_texture_vertices(self):
	x1, y1 = int(self.x), int(self.y)
	x2 = x1 + int(self.width)
	y2 = y1 + int(self.height)
	return [x1, y1, x2, y1, x2, y2, x1, y2]

    def delete(self):
	Control.delete(self)
	if self.texture_vlist is not None:
	    self.texture_vlist.delete()
	    self.texture_vlist = None
	if self.resizer_vlist is not None:
	    self.resizer_vlist.delete()
	    self.resizer_vlist = None
	if self.limits_vlist is not None:
	    self.limits_vlist.delete()
	    self.limits_vlist = None
	self.texture_group = None

    def layout(self, x, y):
	Control.layout(self, x, y)
	self.texture_vlist.vertices = self._get_texture_vertices()
	self.resizer_vlist.vertices = self._get_resizer_vertices()
	self.limits_vlist.vertices = self._get_limits_vertices()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
	if not self.is_dragging:
	    return

	dx = float(dx) / self.scale
	dy = float(dy) / self.scale
	x, y, width, height = self.region
	left = x
	right = x + width
	bottom = y
	top = y + height
	if self.corner == kytten.ANCHOR_TOP_LEFT:  # stretch up and left
	    x = min(x + dx, right)
	    width = right - x
	    height = max(height + dy, 0)
	elif self.corner == kytten.ANCHOR_LEFT:  # stretch left only
	    x = min(x + dx, x + width)
	    width = right - x
	elif self.corner == kytten.ANCHOR_BOTTOM_LEFT:  # down and left
	    x = min(x + dx, right)
	    y = min(y + dy, top)
	    width = right - x
	    height = top - y
	elif self.corner == kytten.ANCHOR_TOP:  # stretch up only
	    height = max(height + dy, 0)
	elif self.corner == kytten.ANCHOR_BOTTOM:  # stretch down only
	    y = min(y + dy, top)
	    height = top - y
	elif self.corner == kytten.ANCHOR_TOP_RIGHT:  # stretch up and right
	    width = max(width + dx, 0)
	    height = max(height + dy, 0)
	elif self.corner == kytten.ANCHOR_RIGHT:  # stretch right only
	    width = max(width + dx, 0)
	elif self.corner == kytten.ANCHOR_BOTTOM_RIGHT:  # down and right
	    y = min(y + dy, top)
	    width = max(width + dx, 0)
	    height = top - y
	else:  # center or no corner set, drag the whole square!
	    x += dx
	    y += dy
	self.set_region(x, y, width, height, self.color, self.limits)

    def on_mouse_press(self, x, y, button, modifiers):
	self.is_dragging = True
	rx, ry, width, height = self.region
	if width < 20 or height < 20:  # sizer corners on outside
	    x0 = int(self.x + rx * self.scale - 8)
	    y0 = int(self.y + ry * self.scale - 8)
	    x1, y1 = x0 + 8, y0 + 8
	    x2 = x1 + int(width * self.scale)
	    y2 = y1 + int(height * self.scale)
	    x3, y3 = x2 + 8, y2 + 8
	else:                          # sizer corners on inside
	    x0 = int(self.x + rx * self.scale)
	    y0 = int(self.y + ry * self.scale)
	    x1, y1 = x0 + 8, y0 + 8
	    x3 = x0 + int(width * self.scale)
	    y3 = y0 + int(height * self.scale)
	    x2, y2 = x3 - 8, y3 - 8
	self.corner = None
	if x < x1:
	    if y < y1: # lower left corner
		self.corner = kytten.ANCHOR_BOTTOM_LEFT
	    elif y > y2: # upper left corner
		self.corner = kytten.ANCHOR_TOP_LEFT
	    else:
		self.corner = kytten.ANCHOR_LEFT
	elif x > x2:
	    if y < y1: # lower right corner
		self.corner = kytten.ANCHOR_BOTTOM_RIGHT
	    elif y > y2: # upper right corner
		self.corner = kytten.ANCHOR_TOP_RIGHT
	    else:
		self.corner = kytten.ANCHOR_RIGHT
	else:
	    if y < y1: # bottom side
		self.corner = kytten.ANCHOR_BOTTOM
	    elif y > y2: # top side
		self.corner = kytten.ANCHOR_TOP

    def on_mouse_release(self, x, y, button, modifiers):
	self.is_dragging = False
	x, y, width, height = self.region
	self.region = [int(x + 0.5), int(y + 0.5),
		       int(width + 0.5), int(height + 0.5)]
	if self.resizer_vlist is not None:
	    self.resizer_vlist.vertices = self._get_resizer_vertices()
	if self.on_resize is not None:
	    self.on_resize(*self.region)

    def set_region(self, x, y, width, height, color, limits=None):
	self.limits = limits
	self.color = color
	if self.limits is None:
	    left_limit = bottom_limit = 0
	    right_limit, top_limit = self.texture.width, self.texture.height
	else:
	    lx, ly, lwidth, lheight = self.limits
	    left_limit = lx
	    bottom_limit = ly
	    right_limit = left_limit + lwidth
	    top_limit = bottom_limit + lheight
	x = min(max(x, left_limit), right_limit)
	y = min(max(y, bottom_limit), top_limit)
	width = min(width, right_limit - x)
	height = min(height, top_limit - y)
	self.region = [x, y, width, height]
	if self.resizer_vlist is not None:
	    self.resizer_vlist.vertices = self._get_resizer_vertices()
	    self.resizer_vlist.colors = color * 40

    def set_scale(self, scale):
	self.scale = scale
	if self.saved_dialog is not None:
	    self.saved_dialog.set_needs_layout()

    def size(self, dialog):
	Control.size(self, dialog)
	self.width = self.texture.width * self.scale
	self.height = self.texture.height * self.scale
	if self.texture_vlist is None:
	    self.texture_group = pyglet.graphics.TextureGroup(
		self.texture, dialog.fg_group)
	    self.texture_vlist = dialog.batch.add(4, gl.GL_QUADS,
                self.texture_group,
                ('v2i', self._get_texture_vertices()),
                ('c4B', (255, 255, 255, 255) * 4),
		('t3f', self.texture.tex_coords))
	if self.resizer_vlist is None:
	    self.resizer_vlist = dialog.batch.add(40, gl.GL_LINES,
                dialog.highlight_group,
                ('v2i', self._get_resizer_vertices()),
                ('c4B', self.color * 40))
	if self.limits_vlist is None:
	    self.limits_vlist = dialog.batch.add(8, gl.GL_LINES,
                dialog.highlight_group,
                ('v2i', self._get_limits_vertices()),
                ('c4B', (192, 192, 192, 255) * 8))

