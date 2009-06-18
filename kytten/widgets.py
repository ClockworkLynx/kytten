# kytten/widgets.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Simple widgets belong in this file, to avoid cluttering the directory with
# many small files.  More complex widgets should be placed in separate files.

# Widget: the base GUI element.  A fixed area of space.
# Control: a Widget which accepts events.
# Test: a Widget which draws a crossed box within its area.
# Spacer: a Widget which can expand to fill available space.  Useful to
#         push other Widgets in a layout to the far right or bottom.
# Graphic: a Widget with a texture drawn over its surface.  Can be expanded.
# Label: a Widget which wraps a simple text label.

import pyglet
from pyglet import gl

class Widget:
    """
    The base of all Kytten GUI elements.  Widgets correspond to areas on the
    screen and may (in the form of Controls) respond to user input.
    A simple Widget can be used as a fixed-area spacer.

    Widgets are constructed in two passes: first, they are created and
    passed into a Dialog, or added to a Dialog or one of its children,
    then the Dialog calls their size() method to get their size and their
    layout() method to place them on the screen.  When their size is gotten
    for the first time, they initialize any requisite graphic elements
    that could not be done at creation time.
    """
    def __init__(self, width=0, height=0):
        """
        Creates a new Widget.

        @param width Initial width
        @param height Initial height
        """
        self.x = self.y = 0
        self.width = width
        self.height = height
        self.saved_dialog = None

    def _get_controls(self):
        """
        Return this widget if it is a Control, or any children which
        are Controls.
        """
        return []

    def delete(self):
        """
        Deletes any graphic elements we have constructed.  Note that
        we may be asked to recreate them later.
        """
        pass

    def expand(self, width, height):
        """
        Expands the widget to fill the specified space given.

        @param width Available width
        @param height Available height
        """
        assert False, "Widget does not support expand"

    def hit_test(self, x, y):
        """
        True if the given point lies within our area.

        @param x X coordinate of point
        @param y Y coordinate of point
        @returns True if the point is within our area
        """
        return x >= self.x and x < self.x + self.width and \
               y >= self.y and y < self.y + self.height

    def is_expandable(self):
        """
        Returns true if the widget can expand to fill available space.
        """
        return False

    def is_focusable(self):
        """
        Return true if the widget can be tabbed to and accepts keyboard
        input
        """
        return False

    def is_input(self):
        """
        Returns true if the widget accepts an input and can return a value
        """
        return False

    def layout(self, x, y):
        """
        Assigns a new location to this widget.

        @param x X coordinate of our lower left corner
        @param y Y coordinate of our lower left corner
        """
        self.x, self.y = x, y

    def size(self, dialog):
        """
        Constructs any graphic elements needed, and recalculates our size
        if necessary.

        @param dialog The Dialog which contains this Widget
        """
        if dialog != self and dialog is not None:
            self.saved_dialog = dialog

    def teardown(self):
        """
        Removes all resources and pointers to other GUI widgets.
        """
        self.delete()
        self.saved_dialog = None

class Control(Widget, pyglet.event.EventDispatcher):
    """
    Controls are widgets which can accept events.

    Dialogs will search their children for a list of controls, and will
    then dispatch events to whichever control is currently the focus of
    the user's attention.
    """
    def __init__(self, id=None, value=None, width=0, height=0):
        """
        Creates a new Control.

        @param id Controls may have ids, which can be used to identify
                  them to the outside application.
        @param value Controls may be assigned values at start time.  The
                     values of all controls which have ids can be obtained
                     through the containing Dialog.
        @param x Initial X coordinate of lower left corner
        @param y Initial Y coordinate of lower left corner
        @param width Initial width
        @param height Initial height
        """
        Widget.__init__(self, width, height)
        self.id = id
        self.value = value
        pyglet.event.EventDispatcher.__init__(self)
        self.is_highlight = False
        self.is_focus = False

    def _get_controls(self):
        return [self]

    def get_cursor(self, x, y):
        return self.cursor

    def is_focus(self):
        return self.is_focus

    def is_highlight(self):
        return self.is_highlight

    def on_gain_focus(self):
        self.is_focus = True

    def on_gain_highlight(self):
        self.is_highlight = True

    def on_lose_focus(self):
        self.is_focus = False

    def on_lose_highlight(self):
        self.is_highlight = False

# Controls can potentially accept most of the events defined for the window,
# but in practice we'll only pass selected events from Dialog.  This avoids
# a large number of unsightly empty method declarations.
for event_type in pyglet.window.Window.event_types:
    Control.register_event_type(event_type)

Control.register_event_type('on_gain_focus')
Control.register_event_type('on_gain_highlight')
Control.register_event_type('on_lose_focus')
Control.register_event_type('on_lose_highlight')
Control.register_event_type('on_update')

class Test(Widget):
    """
    A simple widget which draws a crossed box.
    """
    def __init__(self, width, height):
        """
        Blocks occupy a fixed width and height.

        @param width Width
        @param height Height
        """
        Widget.__init__(self, width=width, height=height)
        self.vertex_list = None

    def _get_indices(self):
        """
        Defines a square with two crossed diagonals.

        @return An array of indices to update our indexed vertex list.
        """
        return (0, 1, 1, 2, 2, 3, 3, 0, 0, 2, 1, 3)

    def _get_vertices(self):
        """
        Defines the corners of the square.

        @return An array of coordinates for our indexed vertex list.
        """
        x1, y1 = self.x, self.y
        x2, y2 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

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
        Widget.layout(self, x, y)
        self.vertex_list.vertices = self._get_vertices()

    def size(self, dialog):
        """Constructs a vertex list to draw a crossed square.

        @param dialog The Dialog within which we are contained
        """
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.vertex_list is None:
            self.vertex_list = dialog.batch.add_indexed(4, gl.GL_LINES,
                dialog.fg_group,
                self._get_indices(),
                ('v2i', self._get_vertices()),
                ('c4B', dialog.theme['gui_color'] * 4))

class Spacer(Widget):
    """
    A Spacer is an empty widget that expands to fill space in layouts.
    Use Widget if you need a fixed-sized spacer.
    """
    def __init__(self, width=0, height=0):
        """
        Creates a new Spacer.  The width and height given are the minimum
        area that we must cover.

        @param width Minimum width
        @param height Minimum height
        """
        Widget.__init__(self)
        self.min_width, self.min_height = width, height

    def expand(self, width, height):
        """
        Expand the spacer to fill the maximum space.

        @param width Available width
        @param height Available height
        """
        self.width, self.height = width, height

    def is_expandable(self):
        """Indicates the Spacer can be expanded"""
        return True

    def size(self, dialog):
        """Spacer shrinks down to the minimum size for placement.

        @param dialog Dialog which contains us"""
        if dialog is None:
            return
        Widget.size(self, dialog)
        self.width, self.height = self.min_width, self.min_height

class Graphic(Widget):
    """
    Lays out a graphic from the theme, i.e. part of a title bar.
    """
    def __init__(self, component, image_name, is_expandable=False):
        Widget.__init__(self)
        self.component = component
        self.image_name = image_name
        self.expandable=is_expandable
        self.graphic = None
        self.min_width = self.min_height = 0

    def delete(self):
        if self.graphic is not None:
            self.graphic.delete()
            self.graphic = None

    def expand(self, width, height):
        if self.expandable:
            self.width, self.height = width, height
            self.graphic.update(self.x, self.y, self.width, self.height)

    def is_expandable(self):
        return self.expandable

    def layout(self, x, y):
        self.x, self.y = x, y
        self.graphic.update(x, y, self.width, self.height)

    def size(self, dialog):
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.graphic is None:
            template = dialog.theme[self.component][self.image_name]
            self.graphic = template.generate(
                dialog.theme[self.component]['gui_color'],
                dialog.batch,
                dialog.fg_group)
            self.min_width = self.graphic.width
            self.min_height = self.graphic.height
        self.width, self.height = self.min_width, self.min_height

class Label(Widget):
    """A wrapper around a simple text label."""
    def __init__(self, text="", bold=False, italic=False,
                 font_name=None, font_size=None, color=None, component=None):
        Widget.__init__(self)
        self.text = text
        self.bold = bold
        self.italic = italic
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.component = component
        self.label = None

    def delete(self):
        if self.label is not None:
            self.label.delete()
            self.label = None

    def layout(self, x, y):
        Widget.layout(self, x, y)
        font = self.label.document.get_font()
        self.label.x = x
        self.label.y = y - font.descent

    def size(self, dialog):
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.label is None:
            self.label = pyglet.text.Label(
                self.text, bold=self.bold, italic=self.italic,
                color=self.color or dialog.theme[self.component]['gui_color'],
                font_name=self.font_name or
                          dialog.theme[self.component]['font'],
                font_size=self.font_size or
                          dialog.theme[self.component]['font_size'],
                batch=dialog.batch, group=dialog.fg_group)
            font = self.label.document.get_font()
            self.width = self.label.content_width
            self.height = font.ascent - font.descent  # descent is negative

