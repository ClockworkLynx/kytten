# kytten/scrollable.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

from dialog import DialogEventManager
from frame import Wrapper
from scrollbar import HScrollbar, VScrollbar
from widgets import Widget

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
        self.was_scissor_enabled = False

    def set_state(self):
        """
        Enables a scissor test on our region
        """
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT |
                        gl.GL_CURRENT_BIT)
        self.was_scissor_enabled = gl.glIsEnabled(gl.GL_SCISSOR_TEST)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(int(self.x), int(self.y),
                     int(self.width), int(self.height))

    def unset_state(self):
        """
        Disables the scissor test
        """
        if not self.was_scissor_enabled:
            gl.glDisable(gl.GL_SCISSOR_TEST)
        gl.glPopAttrib()

class Scrollable(Wrapper):
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

    def _get_controls(self):
        """
        We represent ourself as a Control to the Dialog, but we pass through
        the events we receive from Dialog.
        """
        base_controls = Wrapper._get_controls(self)
        controls = []
        our_left = self.content_x
        our_right = our_left + self.content_width
        our_bottom = self.content_y
        our_top = our_bottom + self.content_height
        for control, left, right, top, bottom in base_controls:
            controls.append((control,
                             max(left, our_left),
                             min(right, our_right),
                             min(top, our_top),
                             max(bottom, our_bottom)))
        if self.hscrollbar is not None:
            controls += self.hscrollbar._get_controls()
        if self.vscrollbar is not None:
            controls += self.vscrollbar._get_controls()
        return controls

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
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def ensure_visible(self, control):
        """
        Make sure a control is visible.
        """
        offset_x = 0
        if self.hscrollbar:
            offset_x = self.hscrollbar.get(self.content_width,
                                           self.content.width)
        offset_y = 0
        if self.vscrollbar:
            offset_y = self.content.height - self.content_height - \
                     self.vscrollbar.get(self.content_height,
                                         self.content.height)
        control_left = control.x - self.content_x - offset_x
        control_right = control_left + control.width
        control_bottom = control.y - self.content_y + offset_y
        control_top = control_bottom + control.height
        if self.hscrollbar is not None:
            self.hscrollbar.ensure_visible(control_left, control_right,
                                           max(self.content_width,
                                               self.content.width))
        if self.vscrollbar is not None:
            self.vscrollbar.ensure_visible(control_top, control_bottom,
                                           max(self.content_height,
                                               self.content.height))

    def expand(self, width, height):
        if self.content.is_expandable():
            if self.vscrollbar is not None:
                self.content_width = width - self.vscrollbar_width
            else:
                self.content_width = width
            if self.hscrollbar is not None:
                self.content_height = height - self.hscrollbar_height
            else:
                self.content_height = height
            self.content.expand(max(self.content_width, self.content.width),
                                max(self.content_height, self.content.height))
        self.width, self.height = width, height

    def get_root(self):
        if self.saved_dialog:
            return self.saved_dialog.get_root()
        else:
            return self

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
                x + self.content_width, y)

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

        self.needs_layout = False

    def on_update(self, dt):
        """
        On updates, we redo the layout if scrollbars have changed position

        @param dt Time passed since last update event (in seconds)
        """
        if self.needs_layout:
            width, height = self.width, self.height
            self.size(self.saved_dialog)
            self.expand(width, height)
            self.layout(self.x, self.y)

    def set_needs_layout(self):
        self.needs_layout = True
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def set_wheel_hint(self, control):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_hint(control)

    def set_wheel_target(self, control):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_target(control)

    def size(self, dialog):
        """
        Recalculate the size of the Scrollable.

        @param dialog Dialog which contains us
        """
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.is_fixed_size:
            self.width, self.height = self.max_width, self.max_height

        self.hscrollbar_height = \
            dialog.theme['hscrollbar']['left']['image'].height
        self.vscrollbar_width = \
            dialog.theme['vscrollbar']['up']['image'].width

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
        else:
            if self.hscrollbar is not None:
                self.hscrollbar.delete()
                self.hscrollbar = None

        if self.always_show_scrollbars or \
           (self.max_height and self.height > self.max_height):
            if self.vscrollbar is None:
                self.vscrollbar = VScrollbar(self.max_height)
        else:
            if self.vscrollbar is not None:
                self.vscrollbar.delete()
                self.vscrollbar = None

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
