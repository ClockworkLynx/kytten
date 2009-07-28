# theme_editor.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Creates or modifies a .json file for a kytten GUI theme.

import glob
import os
import sys

import pyglet
# Disable error checking for increased performance
pyglet.options['debug_gl'] = False
from pyglet import gl

import kytten
from kytten import safe_eval
from kytten.scrollable import ScrollableGroup
from kytten.theme import TextureGraphicElementTemplate
from kytten.theme import FrameTextureGraphicElementTemplate
from kytten.widgets import Control

# Default theme
gTheme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
    'gui_color': (255, 235, 128, 255),
})

# Constants

IMAGE_REGION_COLOR = (255, 128, 64, 255)
IMAGE_STRETCH_COLOR = (64, 255, 128, 255)
IMAGE_PADDING_COLOR = (64, 128, 255, 255)

# Global Variables

gDirty = False

#
# Editor-specific Widgets
#

class ProxyDialog(kytten.Wrapper):
    """
    Allows us to insert the theme being worked on into our own dialog.
    """
    def __init__(self, content, theme):
	kytten.Wrapper.__init__(self, content)
	self.content = content
	self.theme = theme
	self.batch = None
        self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def delete(self):
	kytten.Wrapper.delete(self)
	self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def get_root(self):
        if self.saved_dialog:
            return self.saved_dialog.get_root()
        else:
            return self

    def set_needs_layout(self):
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return
        kytten.Widget.size(self, dialog)
        if self.root_group is None: # do we need to re-clone dialog groups?
            self.batch = dialog.batch
            self.root_group = dialog.fg_group
            self.panel_group = pyglet.graphics.OrderedGroup(
                0, self.root_group)
            self.bg_group = pyglet.graphics.OrderedGroup(
                1, self.root_group)
            self.fg_group = pyglet.graphics.OrderedGroup(
                2, self.root_group)
            self.highlight_group = pyglet.graphics.OrderedGroup(
                3, self.root_group)
            kytten.Wrapper.delete(self)  # rebuild children
        kytten.Wrapper.size(self, self)  # all children are to use our groups

class Resizable(Control):
    """
    A resizable box.
    """
    def __init__(self, width, height, disabled=False):
        """
        Blocks occupy a fixed width and height.

        @param width Width
        @param height Height
        """
        Control.__init__(self, width=width, height=height, disabled=disabled)
	self.color = None
        self.vertex_list = None
	self.is_dragging = False

    def _get_controls(self):
	if self.width < 20 or self.height < 20:
	    return [(self, self.x, self.x + self.width + 8,
		           self.y + self.height, self.y - 8)]
	else:
	    return Control._get_controls(self)

    def _get_vertices(self):
        """
        Defines the corners of the square.

        @return An array of coordinates for our indexed vertex list.
        """
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
	if self.width < 20 or self.height < 20: # draw drag point on outside
	    x3, y4 = x2, y1
	else:
	    x3, y4 = x2 - 8, y1 + 8
	x4, y3 = x3 + 8, y4 - 8
        return (16, (x1, y1, x2, y1, x2, y1, x2, y2,  # main square
		     x2, y2, x1, y2, x1, y2, x1, y1,
		     x3, y3, x4, y3, x4, y3, x4, y4,  # drag point
		     x4, y4, x3, y4, x3, y4, x3, y3))

    def delete(self):
        """
        Deletes our vertex list.
        """
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def layout(self, x, y):
        """Places the vertex list at the new location.

        @param x X coordinate of our lower left corner
        @param y Y coordinate of our lower left corner
        """
        Control.layout(self, x, y)
	if not self.is_disabled():
	    num_points, self.vertex_list.vertices = self._get_vertices()
	    self.vertex_list.colors = self.color * num_points
	else:
	    self.is_dragging = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
	if not self.is_dragging:
	    return

	self.width = max(int(self.width + dx), 0)
	self.height = max(int(self.height - dy), 0)
	if self.saved_dialog is not None:
	    self.saved_dialog.set_needs_layout()

    def on_mouse_press(self, x, y, button, modifiers):
	self.is_dragging = True

    def on_mouse_release(self, x, y, button, modifiers):
	self.is_dragging = False
	self.corner = None

    def size(self, dialog):
        """Constructs a vertex list to draw a crossed square.

        @param dialog The Dialog within which we are contained
        """
        if dialog is None:
            return
        Control.size(self, dialog)
        if self.vertex_list is None and not self.is_disabled():
	    self.color = dialog.theme['gui_color']
	    num_points, vertices = self._get_vertices()
            self.vertex_list = dialog.batch.add(num_points, gl.GL_LINES,
                dialog.fg_group,
                ('v2i', vertices),
                ('c4B', self.color * num_points))

class ImageRegionPlacer(Control):
    """
    Display an image and a region within the image, which can be
    resized or moved.
    """
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
	self.color = IMAGE_REGION_COLOR
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

#
# StateManager
#

class StateManager():
    """StateManager ensures that only the topmost state is handling events
    for the window at a time.  States are expected to implement these
    functions:
        def on_hide_state(self, window, manager):
	    '''Called when the state is hidden, i.e. another state
	    has been pushed on top.

	    @param window The application window
	    @param manager The StateManager
	    '''

	def on_show_state(self, window, manager):
	    '''Called when the state is visible, i.e. it has just been
	    pushed or a state that was on top has been removed.

	    @param window The application window
	    @param manager The StateManager
	    '''
    """
    def __init__(self, window):
	self.window = window
	self.stack = []

    def _hide_state(self, state):
	self.window.remove_handlers(state)
	if hasattr(state, 'on_hide_state'):
	    state.on_hide_state(self.window, self)

    def _show_state(self, state):
	self.window.push_handlers(state)
	if hasattr(state, 'on_show_state'):
	    state.on_show_state(self.window, self)

    def push(self, state):
	if self.stack:
	    self._hide_state(self.stack[-1])
	self.stack.append(state)
	self._show_state(self.stack[-1])

    def pop(self):
	assert self.stack
	self._hide_state(self.stack[-1])
	retval = self.stack.pop()
	if self.stack:
	    self._show_state(self.stack[-1])
	else:
	    # no more states to show - we're done!
	    pyglet.app.exit()
	return retval

#
# Theme Editor States
#

class NoTexturesException(Exception):
    pass

class BaseState:
    def __init__(self):
	self.dialog = None
	self.window = None
	self.manager = None
	self.popup = None

    def on_draw(self):
	if self.window is not None:
	    self.window.clear()
	if self.dialog is not None:
	    self.dialog.draw()
	if self.popup is not None:
	    self.popup.draw()

    def on_hide_state(self, window, manager):
	if self.popup is not None:
	    self.popup.teardown()
	    self.popup = None
	if self.dialog is not None:
	    self.dialog.teardown()
	    self.dialog = None

    def on_show_state(self, window, manager):
	self.window = window
	self.manager = manager

    def popup_message(self, message):
	def delete_popup(dialog):
		    self.popup = None
	if self.popup is not None:
	    self.popup.teardown()
	self.popup = kytten.PopupMessage(
	    message, theme=gTheme, window=window, on_escape=delete_popup)

class ThemeDirSelectState(BaseState):
    def on_show_state(self, window, manager):
	BaseState.on_show_state(self, window, manager)

	def on_theme_dir_select(filename):
	    if filename:
		self.select_theme_dir(filename)
	    else:
		self.popup_message("Please select a directory")

	def on_theme_dir_cancel(dialog):
	    self.manager.pop()

	self.dialog = kytten.DirectorySelectDialog(
	    title="Select a theme directory",
	    window=window,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=gTheme,
	    on_select=on_theme_dir_select,
	    on_escape=on_theme_dir_cancel)

    def select_theme_dir(self, filename):
	json_files = glob.glob(os.path.join(filename, '*.json'))
	if len(json_files) < 2:
	    if json_files:
		json_filename = os.path.basename(json_files[0])  # first file
		try:
		    self.manager.push(ThemeEditState(filename, json_filename))
		except NoTexturesException:
		    self.popup_message("Directory must contain textures")
	    else:
		self.manager.push(ThemeNewFileState(filename))
	else:
	    self.manager.push(ThemeFileSelectState(filename))

class ThemeFileSelectState(BaseState):
    def __init__(self, theme_dir):
	BaseState.__init__(self)
	self.theme_dir = theme_dir

    def on_show_state(self, window, manager):
	BaseState.on_show_state(self, window, manager)

	def on_theme_file_select(filename):
	    if filename:
		self.select_theme_file(filename)
	    else:
		self.popup_message("Please select a file")

	def on_theme_file_cancel(dialog):
	    self.manager.pop()

	json_files = glob.glob(os.path.join(self.theme_dir, '*.json'))
	json_files = [os.path.basename(x) for x in json_files]
	self.dialog = kytten.Dialog(
	    kytten.TitleFrame("kytten Theme Editor",
		kytten.VerticalLayout([
		    kytten.Label("Please select a theme file"),
		    kytten.Menu(options=['(New File)'] + json_files,
				on_select=on_theme_file_select)
		]),
	    ),
	    window=window,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=gTheme,
	    on_escape=on_theme_file_cancel)

    def select_theme_file(self, filename):
	if filename == '(New File)':
	    self.manager.push(ThemeNewFileState(self.theme_dir))
	else:
	    try:
		self.manager.push(ThemeEditState(self.theme_dir, filename))
	    except NoTexturesException:
		self.popup_message('Directory must contain textures')

class ThemeNewFileState(BaseState):
    def __init__(self, theme_dir):
	BaseState.__init__(self)
	self.theme_dir = theme_dir

    def on_show_state(self, window, manager):
	BaseState.on_show_state(self, window, manager)

	def on_theme_file_cancel(dialog):
	    self.manager.pop()

	def on_theme_file_enter(dialog):
	    form = dialog.get_values()
	    filename = form['name']
	    if filename:
		name = os.path.join(self.theme_dir, filename)
		if os.path.isfile(name):
		    self.popup_message("%s already exists" % filename)
		elif not filename.endswith('.json'):
		    self.popup_message("%s must end in .json" % filename)
		else:
		    self.set_theme_file(filename)
	    else:
		self.popup_message("Please select a file")

	self.dialog = kytten.Dialog(
	    kytten.TitleFrame("kytten Theme Editor",
		kytten.VerticalLayout([
		    kytten.Label("Please select a theme file name"),
		    kytten.Input(id='name')
		]),
	    ),
	    window=window,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=gTheme,
	    on_escape=on_theme_file_cancel,
	    on_enter=on_theme_file_enter)

    def set_theme_file(self, filename):
	try:
	    new_state = ThemeEditState(self.theme_dir, filename)
	    self.manager.pop()
	    self.manager.push(new_state)
	except NoTexturesException:
	    self.popup_message("Directory must contain textures")

class _NodeEditState(BaseState):
    def __init__(self, theme_dir, theme, textures, path=[],
		 on_exit=None):
	BaseState.__init__(self)
	self.theme_dir = theme_dir
	self.theme = theme
	self.textures = textures
	self.path = path
	self.add_button = None
	self.delete_button = None
	self.on_exit = on_exit
	self.file_label = None

    def _get_buttons(self):
	if self.path:
	    disabled = bool(self.theme.get(self.path))
	    def on_return():
		self.manager.pop()
	    def on_delete_click():
		self.do_delete_this()
	    self.delete_button = kytten.Button("Delete Component",
					       disabled=disabled,
					       on_click=on_delete_click)
	    return [kytten.Button("Back", on_click=on_return),
		    self.delete_button]
	else:
	    return []

    def _get_content(self):
	content = [kytten.Label("Theme: %s" % self.theme_dir)]
	if self.path:
	    content += [kytten.Label("Path: %s" % '/'.join(self.path))]
	else:
	    assert hasattr(self, 'name')
	    self.file_label = kytten.Label("File: %s" % self.name)
	    content += [self.file_label]
	content += [kytten.HorizontalLayout(self._get_buttons())]
	content += self._get_image_fields()
	content += self._get_custom_components()
	content += self._get_custom_fields()
	return content

    def _get_custom_components(self):
	# Handle all components without built-in handlers here
	components = []
	items = self.theme[self.path].items()
	items.sort(lambda x, y: cmp(x[0], y[0]))
	for k, v in items:
	    if isinstance(v, dict):
		components.append(k)
	def edit_component(choice):
	    self.do_edit_component(choice)
	def on_add_click():
	    self.do_add_new_component()
	return [kytten.FoldingSection("Custom Components",
	    kytten.VerticalLayout([
		kytten.Menu(options=components,
			    on_select=edit_component,
			    align=kytten.HALIGN_LEFT),
	        kytten.Button("Add Component",
			      on_click=on_add_click)]))]

    def _get_custom_fields(self):
	# Handle all fields here that we don't have a basic handler for
	fields_layout = None
	def on_input(id, value):
	    global gDirty
	    gDirty = True

	    try:
		self.theme[self.path][id] = safe_eval.safe_eval(value)
	    except kytten.safe_eval.Unsafe_Source_Error:
		self.theme[self.path][id] = value
	def on_delete(id):
	    self.do_delete_field(fields_layout, id)
	fields = []
	items = self.theme[self.path].items()
	items.sort(lambda x, y: cmp(x[0], y[0]))
	index = 0
	for k, v in items:
	    if not k.startswith('image') and not isinstance(v, dict):
		fields.append([kytten.Label(k),
			       kytten.Input(id=k, text=str(v),
					    on_input=on_input),
			       kytten.Button("Delete", id=k,
					     on_click=on_delete)])
	    index += 1
	fields_layout = kytten.GridLayout(fields)

	# Pop up a dialog if we want to add a new field
	def on_add_field():
	    self.do_add_new_field(fields_layout, on_input, on_delete)
	return [kytten.FoldingSection("Custom Fields",
		    kytten.VerticalLayout([
			kytten.GridLayout(fields, anchor=kytten.ANCHOR_LEFT),
			kytten.Button("Add Field", on_click=on_add_field),
		    ]))]

    def _get_image_fields(self):
	# Display a menu to choose images to edit
	images  = []
	items = self.theme[self.path].items()
	items.sort(lambda x, y: cmp(x[0], y[0]))
	for k, v in items:
	    if isinstance(v, TextureGraphicElementTemplate):
		assert k.startswith('image')
		images.append(k)
	def edit_image(choice):
	    self.do_edit_image(choice)
	def add_image():
	    self.do_add_new_image()
	return [kytten.FoldingSection("Images",
	    kytten.VerticalLayout([
		kytten.Menu(options=images,
			    on_select=edit_image,
			    align=kytten.HALIGN_LEFT),
	        kytten.Button('Add Image', on_click=add_image)]))]

    def do_add_new_component(self):
	if self.popup is not None:
	    self.popup.teardown()
	def do_cancel_add(dialog=None):
	    self.popup.teardown()
	    self.popup = None
	def do_add_component(dialog=None):
	    global gDirty
	    gDirty = True

	    form = self.popup.get_values()
	    self.popup.teardown()
	    self.popup = None

	    name = form['name']
	    if self.theme[self.path].has_key(name):
		self.popup_message("%s is already a field name!" % name)
		return
	    self.theme[self.path][name] = {}
	    self.manager.push(_NodeEditState(self.theme_dir,
					     self.theme,
					     self.textures,
					     self.path + [name]))

	self.popup = kytten.Dialog(
	    kytten.Frame(
		kytten.VerticalLayout([
		    kytten.HorizontalLayout([
			kytten.Label('Name'),
			kytten.Input(id='name', text='new_component')]),
		    kytten.HorizontalLayout([
			kytten.Button("Add", on_click=do_add_component),
			None,
			kytten.Button("Cancel", on_click=do_cancel_add)
		    ])])),
	    window=self.window, theme=gTheme,
	    on_enter=do_add_component, on_escape=do_cancel_add)

    def do_add_new_field(self, fields_layout, on_input, on_delete):
	if self.popup is not None:
	    self.popup.teardown()
	def do_cancel_add(dialog=None):
	    self.popup.teardown()
	    self.popup = None
	def do_add_field(dialog=None):
	    global gDirty
	    gDirty = True

	    form = self.popup.get_values()
	    self.popup.teardown()
	    self.popup = None

	    name = form['name']
	    if self.theme[self.path].has_key(name):
		self.popup_message("%s is already a field name!" % name)
		return
	    try:
		value = safe_eval.safe_eval(form['value'])
	    except kytten.safe_eval.Unsafe_Source_Error:
		value = form['value']
	    self.theme[self.path][name] = value
	    fields_layout.add_row(
		[kytten.Label(name),
		 kytten.Input(id=name, text=str(value), on_input=on_input),
		 kytten.Button("Delete", id=name, on_click=on_delete)])

	    if not self.delete_button.is_disabled():
		self.delete_button.disable()
	    self.dialog.set_needs_layout()

	self.popup = kytten.Dialog(
	    kytten.Frame(
		kytten.VerticalLayout([
		    kytten.GridLayout([
			[kytten.Label('Name'),
			 kytten.Input(id='name', text='new_field')],
			[kytten.Label('Value'),
			 kytten.Input(id='value', text='new_value')]]),
		    kytten.HorizontalLayout([
			kytten.Button("Add", on_click=do_add_field),
			None,
			kytten.Button("Cancel", on_click=do_cancel_add)
		    ])])),
	    window=self.window, theme=gTheme,
	    on_enter=do_add_field, on_escape=do_cancel_add)

    def do_add_new_image(self):
	if self.popup is not None:
	    self.popup.teardown()
	def do_cancel_add(dialog=None):
	    self.popup.teardown()
	    self.popup = None
	def do_add_image(dialog=None):
	    global gDirty
	    gDirty = True

	    form = self.popup.get_values()
	    self.popup.teardown()
	    self.popup = None

	    name = form['name']
	    if self.theme[self.path].has_key(name):
		self.popup_message("%s is already a field name!" % name)
		return
	    if not name.startswith('image'):
		self.popup_message("Image names must begin with 'image'")
	    texture = self.textures[form['texture']]
	    self.theme[self.path][name] = FrameTextureGraphicElementTemplate(
		self.theme,
		texture,
		[0, 0, texture.width, texture.height],  # stretch
		[0, 0, 0, 0])                           # padding
	    self.manager.push(ImageEditState(self.theme_dir,
					     self.theme,
					     self.textures,
					     self.path,
					     name))

	self.popup = kytten.Dialog(
	    kytten.Frame(
		kytten.VerticalLayout([
		    kytten.GridLayout([
			[kytten.Label('Name'),
			 kytten.Input(id='name', text='image')],
			[kytten.Label('Texture'),
			 kytten.Dropdown(id='texture',
					 options=self.textures.keys(),
					 selected=self.textures.keys()[0])]
		    ]),
		    kytten.HorizontalLayout([
			kytten.Button("Add", on_click=do_add_image),
			None,
			kytten.Button("Cancel", on_click=do_cancel_add)
		    ])])),
	    window=self.window, theme=gTheme,
	    on_enter=do_add_image, on_escape=do_cancel_add)

    def do_delete_field(self, fields_layout, id):
	global gDirty
	gDirty = True

	del self.theme[self.path][id]
	index = 0
	for row in fields_layout.content:
	    if row[1].id == id:
		fields_layout.delete_row(index)
		break
	    index += 1
	if not self.theme[self.path]:
	    if self.delete_button.is_disabled():
		self.delete_button.enable()

    def do_delete_this(self):
	if self.theme[self.path]:
	    self.popup_message("Component must be empty to be deleted")
	else:
	    global gDirty
	    gDirty = True

	    del self.theme[self.path[:-1]][self.path[-1]]
	    self.manager.pop()

    def do_edit_component(self, component):
	self.manager.push(_NodeEditState(self.theme_dir,
					 self.theme,
					 self.textures,
					 self.path + [component]))

    def do_edit_image(self, image):
	self.manager.push(ImageEditState(self.theme_dir, self.theme,
					 self.textures, self.path, image))

    def on_show_state(self, window, manager):
	BaseState.on_show_state(self, window, manager)

	content = self._get_content()
	def on_escape(dialog):
	    self.manager.pop()
	self.dialog = kytten.Dialog(
	    kytten.TitleFrame('kytten Theme Editor',
		kytten.Scrollable(
		    kytten.VerticalLayout(content, align=kytten.HALIGN_LEFT),
		    height=500)
	    ),
	    window=window,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=gTheme,
	    on_escape=self.on_exit or on_escape)

class ThemeEditState(_NodeEditState):
    def __init__(self, theme_dir, name='theme.json'):
	self.name = name
	theme = kytten.Theme(theme_dir, allow_empty_theme=True, name=name)
	textures = {}
	files = glob.glob(os.path.join(theme_dir, '*.png')) + \
		glob.glob(os.path.join(theme_dir, '*.gif'))
	for f in [os.path.basename(x) for x in files]:
	    textures[f] = theme._get_texture(f)
	if not textures:
	    raise NoTexturesException

	_NodeEditState.__init__(self, theme_dir, theme, textures,
				on_exit=self.do_exit)

    def _get_buttons(self):
	def on_save():
	    self.do_save()
	def on_save_as():
	    self.do_save_as()
	def on_new():
	    if gDirty:
		if self.popup is not None:
		    self.popup.teardown()
		self.popup = kytten.PopupConfirm(
		    "Create new theme without saving?",
		    on_ok=self.do_new,
		    theme=gTheme,
		    window=self.window)
	    else:
		self.do_new()
	return [kytten.Button("Save", on_click=on_save),
		kytten.Button("Save As", on_click=on_save_as),
		kytten.Button("New", on_click=on_new)]

    def do_exit(self, dialog=None):
	if gDirty:
	    if self.popup is not None:
		self.popup.teardown()
	    self.popup = kytten.PopupConfirm("Exit without saving?",
					     on_ok=self.do_really_exit,
					     theme=gTheme,
					     window=self.window)
	else:
	    self.do_really_exit()

    def do_new(self, dialog=None):
	self.manager.pop()
	self.manager.push(ThemeNewFileState(self.theme_dir))

    def do_really_exit(self, dialog=None):
	self.manager.pop()

    def do_save(self):
	global gDirty
	gDirty = False

	filename = os.path.join(self.theme_dir, self.name)
	new_filename = os.path.join(self.theme_dir, '%s-new' % self.name)
	old_filename = os.path.join(self.theme_dir, '%s-old' % self.name)
	if os.path.isfile(old_filename):
	    os.unlink(old_filename)
	f = open(new_filename, 'w')
	self.theme.write(f)
	f.close()
	if os.path.isfile(filename):
	    os.rename(filename, old_filename)
	os.rename(new_filename, filename)
	if os.path.isfile(old_filename):
	    os.unlink(old_filename)

	self.popup_message("Saved %s" % self.name)

    def do_save_as(self):
	if self.popup is not None:
	    self.popup.teardown()
	def do_cancel_save_as(dialog):
	    self.popup.teardown()
	    self.popup = None
	def do_set_filename(dialog):
	    form = dialog.get_values()
	    filename = form['name']
	    if filename:
		name = os.path.join(self.theme_dir, filename)
		if os.path.isfile(name):
		    self.popup_message("%s already exists" % filename)
		elif not filename.endswith('.json'):
		    self.popup_message("%s must end in .json" % filename)
		else:
		    self.name = filename
		    self.file_label.label.text = 'File: %s' % self.name
		    self.do_save()
	    else:
		self.popup_message("Please select a file")
	self.popup = kytten.Dialog(
	    kytten.Frame(
		kytten.HorizontalLayout([
		    kytten.Label("Filename"),
		    kytten.Input(id='name')
		])),
	    theme=gTheme, window=self.window,
	    on_enter=do_set_filename,
	    on_escape=do_cancel_save_as)

class ImageEditState(BaseState):
    def __init__(self, theme_dir, theme, textures, path, image):
	BaseState.__init__(self)
	self.theme_dir = theme_dir
	self.theme = theme
	self.textures = textures
	self.path = path
	self.image = image
	self.template = None
	self.region = [0, 0, 0, 0]
	self.stretch = [0, 0, 0, 0]
	self.padding = [0, 0, 0, 0]
	self.state = 'Region'

    def _get_content(self):
	def on_return():
	    self.manager.pop()
	def on_delete():
	    self.do_delete_image()
	def on_change_texture():
	    self.do_change_texture()
	content = [kytten.VerticalLayout([
	    kytten.Document("""Theme: %s
Path: %s
Image: %s
""" % (self.theme_dir, '/'.join(self.path), self.image), width=700),
	    kytten.HorizontalLayout([
		kytten.Button("Back", on_click=on_return),
		kytten.Button("Change Texture", on_click=on_change_texture),
		kytten.Button("Delete Image", on_click=on_delete)
	    ]),
	], align=kytten.HALIGN_LEFT)]

	# Locate the base texture for the template
	self.template = self.theme[self.path][self.image]
	texture_id = self.template.texture.id
	our_texture = None
	our_filename = None
	for texture_name, texture in self.textures.iteritems():
	    if texture.id == texture_id:
		our_filename = texture_name
		our_texture = texture
		break
	assert our_texture is not None

	# Determine the region that we occupy
	x, y = self.template.texture.x, self.template.texture.y
	width, height = self.template.width,self. template.height
	self.region = (x, y, width, height)
	left, right, top, bottom = self.template.margins
	self.stretch = (left, bottom,
			width - right - left, height - top - bottom)
	self.padding = self.template.padding

	# Create the Resizable for the example's content
	example_resizable = Resizable(100, 100)
	def enable_example_resizable(is_checked):
	    if is_checked:
		example_resizable.enable()
	    else:
		example_resizable.disable()

	# Create the example
	example = kytten.Frame(example_resizable,
			       path=self.path,
			       image_name=self.image)

	# Create the ImageRegionPlacer for the editor
	region_placer = None
	def set_region(x, y, width, height):
	    global gDirty
	    gDirty = True

	    if self.state == 'Region':
		# Try to keep stretch area the same but restrict it to
		# the current available region
		ox, oy, _, _ = self.region
		sx, sy, swidth, sheight = self.stretch
		sx += ox
		sy += oy
		if sx < x:
		    swidth = max(0, swidth - x + sx)
		    sx = x
		elif sx > x + width:
		    swidth = 0
		    sx = x + width
		if sy < y:
		    sheight = max(0, sheight - y + sy)
		    sy = y
		elif sy > y + height:
		    sheight = 0
		    sy = y + height
		if (sx - x) + swidth > width:
		    swidth = max(0, width - (sx - x))
		if (sy - y) + sheight > height:
		    sheight = max(0, height - (sy - y))

		self.region = (x, y, width, height)
		self.stretch = (sx - x, sy - y, swidth, sheight)
	    elif self.state == 'Stretch':
		rx, ry, rwidth, rheight = self.region
		self.stretch = (x - rx, y - ry, width, height)
	    else:  # Padding
		rx, ry, rwidth, rheight = self.region
		left = x - rx
		bottom = y - ry
		top = ry + rheight - height - y
		right = rx + rwidth - width - x
		self.padding = (left, right, top, bottom)

	    # Drop our old template and construct a new one
	    x, y, width, height = self.region
	    texture = self.theme._get_texture_region(our_filename,
						     x, y, width, height)
	    self.template = FrameTextureGraphicElementTemplate(
		self.theme, texture, self.stretch, self.padding)
	    self.theme[self.path][self.image] = self.template
	    example.delete()
	    self.dialog.set_needs_layout()
	region_placer = ImageRegionPlacer(texture, x, y, width, height,
					  on_resize=set_region)
	def set_placer_scale(scale):
	    region_placer.set_scale(scale)

	# Create a drop-down to control what region we're setting
	def on_region_select(choice):
	    self.state = choice
	    if choice == 'Region':
		region_placer.set_region(*self.region,
					 color=IMAGE_REGION_COLOR)
	    elif choice == 'Stretch':
		rx, ry, rwidth, rheight = self.region
		x, y, width, height = self.stretch
		region_placer.set_region(x + rx, y + ry, width, height,
					 color=IMAGE_STRETCH_COLOR,
					 limits=self.region)
	    else:  # Padding
		rx, ry, rwidth, rheight = self.region
		left, right, top, bottom = self.padding
		region_placer.set_region(left + rx, bottom + ry,
					 rwidth - left - right,
					 rheight - top - bottom,
					 color=IMAGE_PADDING_COLOR,
					 limits=self.region)
	region_control = kytten.Dropdown(
	    options=['Region', 'Stretch', 'Padding'],
	    selected=self.state,
	    on_select=on_region_select)

	content += [
	    kytten.FoldingSection('Image Region',
		kytten.VerticalLayout([
		    region_control,
		    region_placer,
		    kytten.GridLayout([
			[kytten.Label('Scale'),
			 kytten.Slider(value=1.0,
				       min_value=1.0, max_value=8.0,
				       steps=7, width=400,
				       on_set=set_placer_scale)]
		    ], anchor=kytten.ANCHOR_LEFT)
		], padding=10)),
	    kytten.FoldingSection('Example',
		kytten.VerticalLayout([
		    ProxyDialog(example,
				self.theme),
		    kytten.Checkbox("Show content sizer",
				    on_click=enable_example_resizable,
				    is_checked=True),
		])),
	]
	return content

    def do_change_texture(self):
	if self.popup is not None:
	    self.popup.teardown()
	def do_cancel_change(dialog=None):
	    self.popup.teardown()
	    self.popup = None
	def do_change_texture(dialog=None):
	    global gDirty
	    gDirty = True

	    form = self.popup.get_values()
	    self.popup.teardown()
	    self.popup = None

	    texture = self.textures[form['texture']]
	    self.theme[self.path][self.image] = \
		FrameTextureGraphicElementTemplate(
		    self.theme,
		    texture,
		    [0, 0, texture.width, texture.height],  # stretch
		    [0, 0, 0, 0])                           # padding
	    manager = self.manager
	    manager.pop()
	    manager.push(ImageEditState(self.theme_dir,
					     self.theme,
					     self.textures,
					     self.path,
					     self.image))

	self.popup = kytten.Dialog(
	    kytten.Frame(
		kytten.VerticalLayout([
		    kytten.HorizontalLayout([
			kytten.Label('Texture'),
			kytten.Dropdown(id='texture',
					options=self.textures.keys(),
					selected=self.textures.keys()[0])]),
		    kytten.HorizontalLayout([
			kytten.Button("Change", on_click=do_change_texture),
			None,
			kytten.Button("Cancel", on_click=do_cancel_change)
		    ]),
		])),
	    window=self.window, theme=gTheme,
	    on_enter=do_change_texture, on_escape=do_cancel_change)

    def do_delete_image(self):
	global gDirty
	gDirty = True

	del self.theme[self.path][self.image]
	self.manager.pop()

    def on_show_state(self, window, manager):
	BaseState.on_show_state(self, window, manager)

	def on_escape(dialog):
	    self.manager.pop()
	content = self._get_content()
	self.dialog = kytten.Dialog(
	    kytten.TitleFrame("kytten Image Editor",
		kytten.Scrollable(
		    kytten.VerticalLayout(content),
		    width=750, height=500)
	    ),
	    window=window,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=gTheme,
	    on_escape=on_escape)

if __name__ == '__main__':
    window = pyglet.window.Window(
	800, 600, caption='Kytten Theme Editor', resizable=True, vsync=True)
    batch = pyglet.graphics.Batch()
    bg_group = pyglet.graphics.OrderedGroup(0)
    fg_group = pyglet.graphics.OrderedGroup(1)

    # Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
	window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

    # StateManager keeps track of what we're doing
    manager = StateManager(window)

    # Start off by picking the theme directory
    manager.push(ThemeDirSelectState())

    pyglet.app.run()
