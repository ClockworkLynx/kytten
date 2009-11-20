# resizable.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl
import kytten
from kytten.widgets import Control

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

