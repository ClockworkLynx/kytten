# kytten/scrollable.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

from dialog import DialogEventManager
from frame import Wrapper
from scrollbar import HScrollbar, VScrollbar

class ScrollableGroup(pyglet.graphics.Group):
    """
    We restrict what's shown within a Scrollable by performing a scissor
    test.
    """
    def __init__(self, x, y, width, height, parent=None):
        """Create a new ScrollableGroup

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        @param width Width of scissored region
        @param height Height of scissored region
        @param parent Parent group
        """
        pyglet.graphics.Group.__init__(self, parent)
        self.x, self.y, self.width, self.height = x, y, width, height

    def set_state(self):
        """
        Enables a scissor test on our region
        """
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT |
                        gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(self.x, self.y, self.width, self.height)

    def unset_state(self):
        """
        Disables the scissor test
        """
        gl.glPopAttrib()

class Scrollable(Wrapper, DialogEventManager):
    """
    Wraps a layout or widget and limits it to a maximum, or fixed, size.
    If the layout exceeds the viewable limits then it is truncated and
    scrollbars will be displayed so the user can pan around.
    """
    def __init__(self, content=None, width=None, height=None,
                 is_fixed_size=False, always_show_scrollbars=False):
        """
        Creates a new Scrollable.

        @param content The layout or Widget to be scrolled
        @param width Maximum width, or None
        @param height Maximum height, or None
        @param is_fixed_size True if we should always be at maximum size;
                             otherwise we shrink to match our content
        @param always_show_scrollbars True if we should always show scrollbars
        """
        if is_fixed_size:
            assert width is not None and height is not None
        Wrapper.__init__(self, content)
        DialogEventManager.__init__(self)
        self.max_width = width
        self.max_height = height
        self.is_fixed_size = is_fixed_size
        self.always_show_scrollbars = always_show_scrollbars
        self.hscrollbar = None
        self.vscrollbar = None
        self.content_width = 0
        self.content_height = 0
        self.content_x = 0
        self.content_y = 0
        self.hscrollbar_height = 0
        self.vscrollbar_width = 0

        # We emulate some aspects of Dialog here.  We cannot just inherit
        # from Dialog because pyglet event handling won't allow keyword
        # arguments to be passed through.
        self.theme = None
        self.batch = None
        self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None
        self.needs_layout = False
        self.controls = []

    def _get_controls(self):
        """
        We represent ourself as a Control to the Dialog, but we pass through
        the events we receive from Dialog.
        """
        controls = []
        if self.hscrollbar is not None:
            controls += [self.hscrollbar]
        if self.vscrollbar is not None:
            controls += [self.vscrollbar]
        return controls + [self]

    def delete(self):
        """
        Delete all graphical elements associated with the Scrollable
        """
        Wrapper.delete(self)
        if self.hscrollbar is not None:
            self.hscrollbar.delete()
            self.hscrollbar = None
        if self.vscrollbar is not None:
            self.vscrollbar.delete()
            self.vscrollbar = None
        self.root_group = None

    def expand(self, width, height):
        if self.content.is_expandable():
            content_width = max(self.max_width or
                                width-self.vscrollbar_width,
                                self.content.width)
            content_height = max(self.max_height or
                                 height-self.hscrollbar_height,
                                 self.content.height)
            self.content.expand(content_width, content_height)
            if self.vscrollbar is not None:
                self.content_width = width - self.vscrollbar_width
            else:
                self.content_width = width
            if self.hscrollbar is not None:
                self.content_height = height - self.hscrollbar_height
            else:
                self.hscrollbar_height = height
        self.width, self.height = width, height

    def hit_test(self, x, y):
        """
        We only intercept events for the content region, not for
        our scrollbars.  They can handle themselves!
        """
        return x >= self.content_x and y >= self.content_y and \
               x < self.content_x + self.content_width and \
               y < self.content_y + self.content_height

    def is_expandable(self):
        return True

    def layout(self, x, y):
        """
        Reposition the Scrollable

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        self.x, self.y = x, y

        # Work out the adjusted content width and height
        if self.hscrollbar is not None:
            self.hscrollbar.layout(x, y)
            y += self.hscrollbar.height
        if self.vscrollbar is not None:
            self.vscrollbar.layout(
                x + (self.max_width or self.content_width), y)

        # Set the scissor group
        self.root_group.x, self.root_group.y = x - 1, y - 1
        self.root_group.width = self.content_width + 1
        self.root_group.height = self.content_height + 1

        # Work out the content layout
        self.content_x, self.content_y = x, y
        left = x
        top = y + self.content_height - self.content.height
        if self.hscrollbar:
            left -= self.hscrollbar.get(self.content_width,
                                        self.content.width)
        if self.vscrollbar:
            top += self.vscrollbar.get(self.content_height,
                                       self.content.height)
        self.content.layout(left, top)

    def on_lose_focus(self, dialog):
        """
        If we're no longer focused by the Dialog, remove our own focus
        """
        self.set_focus(dialog, None)

    def on_lose_highlight(self, dialog):
        """
        If we're no longer highlighted by the Dialog, remove our own
        highlight
        """
        self.set_hover(dialog, None)

    def on_update(self, dialog, dt):
        """
        On updates, we redo the layout if scrollbars have changed position

        @param dt Time passed since last update event (in seconds)
        """
        if self.needs_layout:
            self.size(dialog)
            self.layout(self.x, self.y)
            self.needs_layout = False
        for control in self.controls:
            control.dispatch_event('on_update', self, dt)

    def set_needs_layout(self):
        self.needs_layout = True

    def size(self, dialog):
        """
        Recalculate the size of the Scrollable.

        @param dialog Dialog which contains us
        """
        if self.is_fixed_size:
            self.width, self.height = self.max_width, self.max_height

        self.hscrollbar_height = \
            dialog.theme['hscrollbar']['image-left'].height
        self.vscrollbar_width = \
            dialog.theme['vscrollbar']['image-up'].width

        if self.root_group is None: # do we need to re-clone dialog groups?
            self.theme = dialog.theme
            self.batch = dialog.batch
            self.root_group = ScrollableGroup(0, 0, self.width, self.height,
                                              parent=dialog.fg_group)
            self.panel_group = pyglet.graphics.OrderedGroup(
                0, self.root_group)
            self.bg_group = pyglet.graphics.OrderedGroup(
                1, self.root_group)
            self.fg_group = pyglet.graphics.OrderedGroup(
                2, self.root_group)
            self.highlight_group = pyglet.graphics.OrderedGroup(
                3, self.root_group)
            Wrapper.delete(self)  # force children to abandon old groups

        Wrapper.size(self, self)  # all children are to use our groups

        if self.always_show_scrollbars or \
           (self.max_width and self.width > self.max_width):
            if self.hscrollbar is None:
                self.hscrollbar = HScrollbar(self.max_width)

        if self.always_show_scrollbars or \
           (self.max_height and self.height > self.max_height):
            if self.vscrollbar is None:
                self.vscrollbar = VScrollbar(self.max_height)

        self.width = min(self.max_width or self.width, self.width)
        self.content_width = self.width
        self.height = min(self.max_height or self.height, self.height)
        self.content_height = self.height

        if self.hscrollbar is not None:
            self.hscrollbar.size(dialog)
            self.hscrollbar.set(self.max_width, max(self.content.width,
                                                    self.max_width))
            self.height += self.hscrollbar.height

        if self.vscrollbar is not None:
            self.vscrollbar.size(dialog)
            self.vscrollbar.set(self.max_height, max(self.content.height,
                                                     self.max_height))
            self.width += self.vscrollbar.width

        self.controls = self.content._get_controls()

