# color_selector.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import math
import pyglet
from pyglet import gl

import kytten
from kytten.button import Button
from kytten.dialog import Dialog
from kytten.frame import Frame
from kytten.layout import ANCHOR_CENTER, VerticalLayout, HorizontalLayout
from kytten.slider import Slider
from kytten.text_input import Input
from kytten.widgets import Control, Label

class ColorWheel(Control):
    """
    Depicts a circle which can be used to select an RGB color.
    """
    path = ['colorselector', 'crosshair']

    RADIUS = 164
    INNER_RADIUS = 132
    BORDER = 4
    VECTORS = []
    NUM_SEGMENTS = int(2 * math.pi * (RADIUS + BORDER) / 24) * 6
    for x in xrange(0, NUM_SEGMENTS):
	angle = float(x) * 2.0 * math.pi / float(NUM_SEGMENTS)
	VECTORS.append((math.cos(angle), math.sin(angle)))
    NUM_ARC_SEGMENTS = NUM_SEGMENTS / 6
    COLORS = []
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([255, x * 255 / NUM_ARC_SEGMENTS, 0])
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([255 - (x * 255 / NUM_ARC_SEGMENTS), 255, 0])
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([0, 255, x * 255 / NUM_ARC_SEGMENTS])
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([0, 255 - (x * 255 / NUM_ARC_SEGMENTS), 255])
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([x * 255 / NUM_ARC_SEGMENTS, 0, 255])
    for x in xrange(0, NUM_ARC_SEGMENTS):
	COLORS.append([255, 0, 255 - (x * 255 / NUM_ARC_SEGMENTS)])

    def __init__(self, color, id=None, on_select=None):
	Control.__init__(self, id=id)
	self.alpha = color[3]
	self.tip_color = [0, 0, 0]
	self.on_select = on_select
	self.circle_vlist = None
	self.inner_circle_vlist = None
	self.inner_circle_bg_vlist = None
	self.colors_vlist = None
	self.triangle_vlist = None
	self.crosshair = None
	self.tri_angle = 0.0
	self.point = (0, 0)
	self.is_turning = False
	self.is_dragging = False
	self.center_x = 0
	self.center_y = 0
	self.pointer_i = 1.0
	self.pointer_j = 0.0
	self.vector_i = [0, 1]
	self.vector_j = [1, 0]
	self.point_a = [0, 0]

	self.set_color(color)

    def _get_vertices(self, center_x, center_y, inner_radius, outer_radius):
	vertices = []
	lastVec = self.VECTORS[-1]
	for xVec, yVec in self.VECTORS:
	    lastXVec, lastYVec = lastVec
	    vertices.extend([center_x + lastXVec * inner_radius,
			     center_y + lastYVec * inner_radius,
			     center_x + xVec * inner_radius,
			     center_y + yVec * inner_radius,
			     center_x + xVec * outer_radius,
			     center_y + yVec * outer_radius,
			     center_x + lastXVec * outer_radius,
			     center_y + lastYVec * outer_radius])
	    lastVec = (xVec, yVec)

	return vertices

    def _get_circle_vlist_vertices(self):
	radius = self.RADIUS + self.BORDER
	innerRadius = self.INNER_RADIUS - self.BORDER
	return self._get_vertices(self.center_x, self.center_y,
				  innerRadius, radius)

    def _get_inner_circle_vlist_vertices(self):
	center_x = self.center_x
	center_y = self.center_y
	inner_radius = self.INNER_RADIUS - self.BORDER
	vertices = []
	lastVec = self.VECTORS[-1]
	for xVec, yVec in self.VECTORS:
	    lastXVec, lastYVec = lastVec
	    vertices.extend([center_x, center_y,
			     center_x + lastXVec * inner_radius,
			     center_y + lastYVec * inner_radius,
			     center_x + xVec * inner_radius,
			     center_y + yVec * inner_radius])
	    lastVec = (xVec, yVec)
	return vertices

    def _get_inner_circle_bg_vlist_colors(self):
	num_segments = self.NUM_SEGMENTS / 6
	return [255, 255, 255, 255] * (3 * num_segments) + \
	       [0, 0, 0, 255] * (3 * num_segments) + \
	       [255, 255, 255, 255] * (3 * num_segments) + \
	       [0, 0, 0, 255] * (3 * num_segments) + \
	       [255, 255, 255, 255] * (3 * num_segments) + \
	       [0, 0, 0, 255] * (3 * num_segments)

    def _get_colors_vlist_vertices(self):
	radius = self.RADIUS
	innerRadius = self.INNER_RADIUS
	return self._get_vertices(self.center_x, self.center_y,
				  innerRadius, radius)

    def _get_colors_vlist_colors(self):
	colors = []
	lastColor = self.COLORS[-1]
	for color in self.COLORS:
	    colors.extend(lastColor)
	    colors.extend(color * 2)
	    colors.extend(lastColor)
	    lastColor = color
	return colors

    def _get_triangle_vlist_vertices(self):
	radius = self.INNER_RADIUS - self.BORDER
	centerX = self.center_x
	centerY = self.center_y
	cosA = math.cos(self.tri_angle + math.pi * 2 / 3)
	sinA = math.sin(self.tri_angle + math.pi * 2 / 3)
	cosB = math.cos(self.tri_angle)
	sinB = math.sin(self.tri_angle)
	cosC = math.cos(self.tri_angle + math.pi * 4 / 3)
	sinC = math.sin(self.tri_angle + math.pi * 4 / 3)
	xA = centerX + cosA * self.INNER_RADIUS
	yA = centerY + sinA * self.INNER_RADIUS
	xB = centerX + cosB * self.INNER_RADIUS
	yB = centerY + sinB * self.INNER_RADIUS
	xC = centerX + cosC * self.INNER_RADIUS
	yC = centerY + sinC * self.INNER_RADIUS
	self.point_a = [xA, yA]
	self.vector_i = [xB - xA, yB - yA]
	self.vector_j = [xC - xA, yC - yA]
	return [xB, yB,
		xA, yA,
		xC, yC,
		centerX + cosB * radius, centerY + sinB * radius,
		centerX + cosA * radius, centerY + sinA * radius,
		centerX + cosC * radius, centerY + sinC * radius]

    def _get_triangle_vlist_colors(self):
	pi_3 = math.pi / 3
	angle = self.tri_angle
	if angle < 0:
	    angle += math.pi * 2
	fract_angle = math.fmod(angle, pi_3)
	sect = int(angle / pi_3)
	fract255 = int(fract_angle * 255 / pi_3)
	if sect < 1:           #   0 to 60  degrees, red -> red+green
	    color = [255, fract255, 0]
	elif sect < 2:         #  60 to 120 degrees, red+green -> green
	    color = [255 - fract255, 255, 0]
	elif sect < 3:         # 120 to 180 degrees, green -> green+blue
	    color = [0, 255, fract255]
	elif sect < 4:         # 180 to 240 degrees, green+blue -> blue
	    color = [0, 255 - fract255, 255]
	elif sect < 5:         # 240 to 300 degrees, blue -> blue+red
	    color = [fract255, 0, 255]
	else:                   # 300 to 360 degrees, blue+red -> red
	    color = [255, 0, 255 - fract255]
	self.tip_color = color
	return [255, 255, 255] * 3 + color + [0, 0, 0] + [255, 255, 255]

    def _update_crosshair(self, set_color=True):
	x, y = self.point_a
	xI, yI = self.vector_i
	xJ, yJ = self.vector_j
	if self.crosshair is not None:
	    width, height = self.crosshair.get_needed_size(0, 0)
	    self.crosshair.update(
		x + xI * self.pointer_i + xJ * self.pointer_j - width/2,
		y + yI * self.pointer_i + yJ * self.pointer_j - width/2,
		width, height)
	rI, gI, bI = self.tip_color
	if set_color:
	    self.color = [
		int(min(self.pointer_i * rI + self.pointer_j * 255, 255)),
		int(min(self.pointer_i * gI + self.pointer_j * 255, 255)),
		int(min(self.pointer_i * bI + self.pointer_j * 255, 255)),
		int(self.alpha)]
	    if self.on_select:
		if self.id is not None:
		    self.on_select(id, self.color)
		else:
		    self.on_select(self.color)
	if self.inner_circle_vlist is not None:
	    self.inner_circle_vlist.colors = \
		self.color * (self.NUM_SEGMENTS * 3)

    def _update_triangle(self):
	if self.triangle_vlist is not None:
	    self.triangle_vlist.vertices = self._get_triangle_vlist_vertices()
	    self.triangle_vlist.colors = self._get_triangle_vlist_colors()

    def delete(self):
	if self.circle_vlist is not None:
	    self.circle_vlist.delete()
	    self.circle_vlist = None
	if self.inner_circle_vlist is not None:
	    self.inner_circle_vlist.delete()
	    self.inner_circle_vlist = None
	if self.inner_circle_bg_vlist is not None:
	    self.inner_circle_bg_vlist.delete()
	    self.inner_circle_bg_vlist = None
	if self.colors_vlist is not None:
	    self.colors_vlist.delete()
	    self.colors_vlist = None
	if self.triangle_vlist is not None:
	    self.triangle_vlist.delete()
	    self.triangle_vlist = None
	if self.crosshair is not None:
	    self.crosshair.delete()
	    self.crosshair = None

    def hit_test(self, x, y):
	dX = x - self.center_x
	dY = y - self.center_y
	radius = math.sqrt(dX * dX + dY * dY)
	if radius <= (self.RADIUS + self.BORDER):
	    return True

    def layout(self, x, y):
	Control.layout(self, x, y)
	radius = self.RADIUS + self.BORDER
	self.center_x = self.x + radius
	self.center_y = self.y + radius

	if self.circle_vlist is not None:
	    self.circle_vlist.vertices = self._get_circle_vlist_vertices()
	if self.inner_circle_vlist is not None:
	    self.inner_circle_vlist.vertices = \
		self._get_inner_circle_vlist_vertices()
	if self.inner_circle_bg_vlist is not None:
	    self.inner_circle_bg_vlist.vertices = \
		self._get_inner_circle_vlist_vertices()
	if self.colors_vlist is not None:
	    self.colors_vlist.vertices = self._get_colors_vlist_vertices()
	if self.triangle_vlist is not None:
	    self.triangle_vlist.vertices = self._get_triangle_vlist_vertices()
	    self.triangle_vlist.colors = self._get_triangle_vlist_colors()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
	if self.is_turning:
	    self.pointer_i = 1
	    self.pointer_j = 0
	    dX = x - self.center_x
	    dY = y - self.center_y
	    self.tri_angle = math.atan2(dY, dX)
	    self._update_triangle()
	elif self.is_dragging:
	    ax, ay = self.point_a
	    x = x - ax
	    y = y - ay
	    a, b = self.vector_i
	    c, d = self.vector_j
	    i = min(max((d * x - c * y) / (d * a - b * c), 0), 1)
	    j = min(max((a * y - b * x) / (a * d - b * c), 0), 1)
	    if (i + j) > 1.0:
		s = 1.0 / (i + j)
		i = i * s
		j = j * s
	    self.pointer_i = i
	    self.pointer_j = j
	self._update_crosshair()

    def on_mouse_press(self, x, y, button, modifiers):
	dX = x - self.center_x
	dY = y - self.center_y
	radius = math.sqrt(dX * dX + dY * dY)
	if radius >= self.INNER_RADIUS:
	    self.is_turning = True
	    self.is_dragging = False
	else:
	    self.is_dragging = True
	    self.is_turning = False
	self.on_mouse_drag(x, y, 0, 0, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
	self.is_turning = False
	self.is_dragging = False

    def set_alpha(self, alpha):
	self.alpha = alpha
	self.color = self.color[0:3] + [alpha]
	self._update_triangle()
	self._update_crosshair()

    def set_color(self, color):
	r, g, b, a = color
	self.alpha = a
	x, y, z = r, g, b

	if r == g and g == b:  # If it's plain grayscale, any angle works
	    angle = 0
	    i = 0
	    j = float(r) / 255.0
	else:
	    # We normalize the color to its extreme, i.e. 128, 64, 64 would
	    # be normalized to 255, 128, 128 to show the color that would
	    # pertain at the tip
	    highest = max(r, max(g, b))
	    if highest != 255:
		r = r * 255 / highest
		g = g * 255 / highest
		b = b * 255 / highest

	    # Now determine the triangle angle and tip color
	    sector = math.pi / 3
	    if r == 255:
		if g > b:   #   0-60:  r = 255,   g = 0-255, b = 0
		    angle = sector * g / 255
		    b = 0
		    j = float(z) / 255.0
		    x = x - z
		    y = y - z
		    z = 0
		    if x == 255:  # red is maxed, use green to calculate
			i = float(y) / float(g)
		    else:
			i = float(x) / float(r)
		else:       # 300-360: r = 255,   g = 0,     b = 255-0
		    angle = sector * 5 + sector * (255 - b) / 255
		    g = 0
		    j = float(y) / 255.0
		    x = x - y
		    z = z - y
		    y = 0
		    if x == 255:  # red is maxed, use blue to calculate
			if z == 0:  # oops, they're both zero.  Psych!
			    i = 1.0
			else:
			    i = float(z) / float(b)
		    else:
			i = float(x) / float(r)
	    elif g == 255:
		if r > b:   #  60-120: r = 255-0, g = 255,   b = 0
		    angle = sector + sector * (255 - r) / 255
		    b = 0
		    j = float(z) / 255.0
		    x = x - z
		    y = y - z
		    z = 0
		    if y == 255:  # green is maxed, use red to calculate
			i = float(x) / float(r)
		    else:
			i = float(y) / float(g)
		else:       # 120-180: r = 0,     g = 255,   b = 0-255
		    angle = sector * 2 + sector * b / 255
		    r = 0
		    j = float(x) / 255.0
		    y = y - x
		    z = z - x
		    x = 0
		    if y == 255:  # green is maxed, use blue to calculate
			if z == 0:  # oops, both red and blue are zero
			    i = 1.0
			else:
			    i = float(z) / float(b)
		    else:
			i = float(y) / float(g)
	    elif b == 255:
		if g > r:   # 180-240: r = 0,     g = 255-0, b = 255
		    angle = sector * 3 + sector * (255 - g) / 255
		    r = 0
		    j = float(x) / 255.0
		    y = y - x
		    z = z - x
		    x = 0
		    if z == 255:  # blue is maxed, use green to calculate
			i = float(y) / float(g)
		    else:
			i = float(z) / float(b)
		else:       # 240-300: r = 0-255, g = 0,     b = 255
		    angle = sector * 4 + sector * r / 255
		    g = 0
		    j = float(y) / 255.0
		    x = x - y
		    z = z - y
		    y = 0
		    if z == 255:  # blue is maxed, use red to calculate
			if x == 0:  # oops, both green and red are zero
			    i = 1.0
			else:
			    i = float(x) / float(r)
		    else:
			i = float(z) / float(b)

	self.pointer_i = i
	self.pointer_j = j
	self.tri_angle = angle
	self.color = color
	self._update_triangle()
	self._update_crosshair(set_color=False)

    def size(self, dialog):
	Control.size(self, dialog)
	self.width = 2 * (self.RADIUS + self.BORDER)
	self.height = self.width
	if self.circle_vlist is None:
	    self.circle_vlist = dialog.batch.add(4 * self.NUM_SEGMENTS,
		gl.GL_QUADS,
                dialog.fg_group,
                ('v2f', self._get_circle_vlist_vertices()),
                ('c4B', [255, 255, 255, 255] * (4 * self.NUM_SEGMENTS)))
	if self.inner_circle_vlist is None:
	    self.inner_circle_vlist = dialog.batch.add(3 * self.NUM_SEGMENTS,
		gl.GL_TRIANGLES,
		dialog.fg_group,
		('v2f', self._get_inner_circle_vlist_vertices()),
		('c4B', self.color * (3 * self.NUM_SEGMENTS)))
	if self.inner_circle_bg_vlist is None:
	    self.inner_circle_bg_vlist = dialog.batch.add(
		3 * self.NUM_SEGMENTS,
		gl.GL_TRIANGLES,
		dialog.bg_group,
		('v2f', self._get_inner_circle_vlist_vertices()),
		('c4B', self._get_inner_circle_bg_vlist_colors()))
	if self.colors_vlist is None:
	    self.colors_vlist = dialog.batch.add(4 * self.NUM_SEGMENTS,
		gl.GL_QUADS,
                dialog.fg_group,
                ('v2f', self._get_colors_vlist_vertices()),
                ('c3B', self._get_colors_vlist_colors()))
	if self.triangle_vlist is None:
	    self.triangle_vlist = dialog.batch.add(6, gl.GL_TRIANGLES,
		dialog.highlight_group,
		('v2f', self._get_triangle_vlist_vertices()),
		('c3B', self._get_triangle_vlist_colors()))
	if self.crosshair is None:
	    self.crosshair = dialog.theme[self.path]['image'].generate(
                [255, 255, 255, 255],
                dialog.batch,
                dialog.highlight_group)

class ColorSelector(Control):
    """
    Depicts a small color-filled box.  When clicked upon, creates a pop-up
    dialog which can be used to set the color.
    """
    path = ['colorselector', 'swatch']

    def __init__(self, color, width=16, height=16,
		 id=None, on_select=None):
	Control.__init__(self, id=id)
	self.color = color
	self.content_width = width
	self.content_height = height
	self.swatch_label = None
	self.swatch = None
	self.vlist = None
	self.on_select = on_select
	self.select_dialog = None
	self.wheel = None
	self.red_input = None
	self.green_input = None
	self.blue_input = None
	self.slider = None
	self.accept_button = None
	self.cancel_button = None

    def _delete_select_dialog(self):
        if self.select_dialog is not None:
            self.select_dialog.window.remove_handlers(self.select_dialog)
            self.select_dialog.teardown()
            self.select_dialog = None
	    self.wheel = None
	    self.red_input = None
	    self.green_input = None
	    self.blue_input = None
	    self.slider = None
	    self.accept_button = None
	    self.cancel_button = None

    def _get_vlist_vertices(self):
	if self.swatch is None:
	    return [0, 0, 0, 0, 0, 0, 0, 0]
	x, y, width, height = self.swatch.get_content_region()
	return [x, y, x + width, y, x + width, y + height, x, y + height]

    def delete(self):
	Control.delete(self)
	if self.swatch_label is not None:
	    self.swatch_label.delete()
	    self.swatch_label = None
	if self.swatch is not None:
	    self.swatch.delete()
	    self.swatch = None  # deleted as part of layout
	if self.vlist is not None:
	    self.vlist.delete()
	    self.vlist = None
	self._delete_select_dialog()

    def layout(self, x, y):
	Control.layout(self, x, y)
	if self.swatch is not None:
	    width, height = self.swatch.get_needed_size(
		self.content_width, self.content_height)
	    self.swatch.update(self.x, self.y, width, height)
	    if self.vlist is not None:
		self.vlist.vertices = self._get_vlist_vertices()
	if self.swatch_label is not None:
	    self.swatch_label.layout(
		x + self.swatch.width + 4,
		y + (self.height - self.swatch_label.height) / 2)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.is_disabled():
            return

        if self.select_dialog is not None:
            self._delete_select_dialog()  # if it's already up, close it
            return

        # Setup some callbacks for the dialog
        root = self.saved_dialog.get_root()

        def on_escape(dialog):
            self._delete_select_dialog()

        def on_color_set(color):
            self.color = color
	    if self.red_input is not None:
		self.red_input.set_text(str(color[0]))
	    if self.green_input is not None:
		self.green_input.set_text(str(color[1]))
	    if self.blue_input is not None:
		self.blue_input.set_text(str(color[2]))

	def on_red_set(red):
	    red = min(max(int(red), 0), 255)
	    print "red = %s" % red
	    self.color = [red] + self.color[1:]
	    self.wheel.set_color(self.color)

	def on_green_set(green):
	    green = min(max(int(green), 0), 255)
	    print "green = %s" % green
	    self.color = [self.color[0], green] + self.color[2:]
	    self.wheel.set_color(self.color)

	def on_blue_set(blue):
	    blue = min(max(int(blue), 0), 255)
	    print "blue = %s" % blue
	    self.color = self.color[:2] + [blue, self.color[3]]
	    self.wheel.set_color(self.color)

	def on_alpha_set(alpha):
	    self.wheel.set_alpha(int(alpha))

	def on_set_color_button():
	    if self.on_select is not None:
		if self.id is not None:
		    self.on_select(self.id, repr(self.color))
		else:
		    self.on_select(repr(self.color))
            if self.vlist is not None:
                self.vlist.delete()
                self.vlist = None
	    if self.swatch_label is not None:
		self.swatch_label.set_text(repr(self.color))
            self._delete_select_dialog()
            self.saved_dialog.set_needs_layout()

	def on_cancel_button():
            self._delete_select_dialog()
            self.saved_dialog.set_needs_layout()

        # We'll need the root window to get window size
        width, height = root.window.get_size()

        # Now to setup the dialog
	self.wheel = ColorWheel(self.color, on_select=on_color_set)
	self.slider = Slider(value=self.wheel.alpha,
			     min_value=0.0, max_value=255.0,
			     steps=8, width=256, on_set=on_alpha_set)
	self.accept_button = Button("Set Color", on_click=on_set_color_button)
	self.cancel_button = Button("Cancel", on_click=on_cancel_button)
	self.red_input = Input(text=str(self.color[0]), on_input=on_red_set,
			       length=3, max_length=3)
	self.green_input = Input(text=str(self.color[1]),
				 on_input=on_green_set, length=3, max_length=3)
	self.blue_input = Input(text=str(self.color[2]), on_input=on_blue_set,
				length=3, max_length=3)
        self.select_dialog = Dialog(
            Frame(
		VerticalLayout([
		    self.wheel,
		    HorizontalLayout([
			Label("Red"), self.red_input, None,
			Label("Green"), self.green_input, None,
			Label("Blue"), self.blue_input
		    ]),
		    HorizontalLayout([
			Label("Alpha"),
			self.slider,
		    ]),
		    HorizontalLayout([
			self.accept_button, None, self.cancel_button
		    ]),
		])
            ),
            window=root.window, batch=root.batch,
            group=root.root_group.parent, theme=root.theme,
            movable=True, anchor=ANCHOR_CENTER,
            on_escape=on_escape)
        root.window.push_handlers(self.select_dialog)

    def size(self, dialog):
	Control.size(self, dialog)
	if self.swatch is None:
	    self.swatch = dialog.theme[self.path]['image'].generate(
                dialog.theme[self.path]['gui_color'],
                dialog.batch,
                dialog.fg_group)
	if self.vlist is None:
	    self.vlist = dialog.batch.add(4, gl.GL_QUADS,
                dialog.highlight_group,
                ('v2i', self._get_vlist_vertices()),
                ('c4B', self.color * 4))
	if self.swatch_label is None:
	    self.swatch_label = Label(repr(self.color))
	self.swatch_label.size(dialog)
	swatch_width, swatch_height = self.swatch.get_needed_size(
	    self.content_width, self.content_height)
	self.height = max(self.swatch_label.height, swatch_height)
	self.width = swatch_width + 4 + self.swatch_label.width

    def teardown(self):
	Control.teardown(self)
	if self.select_dialog is not None:
	    self.select_dialog.teardown()
	    self.select_dialog = None