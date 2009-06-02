# kytten/gui.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

"""
This module implements the dialog which directs focus and events between
its contained GUI elements, and the panel which can enclose the dialog.

Individual widgets are defined under widget.py.

In general, all GUI elements are sized and laid out as follows:

* The Dialog asks its content to calculate its size.  This may be a
  recursive procedure.
* If necessary, contained elements can now create vertex lists based on
  the dialog's batch and group.  They did not have access to this at
  construction time.
* Once all elements have been sized, the Dialog now knows its correct size.
  It repositions itself on the screen, then passes this root location to
  its contained elements.
* Contained elements set their sizes and update vertex lists, then repeat for
  elements they contain.

Mouse and keyboard events are handled as follows:

* Any control may be hovered.  We pass 'on_gain_highlight' and
  'on_lose_highlight' events to affected controls.
* Controls which are clicked are said to have focus.  They retain this
  until the user clicks elsewhere.  Thus, we always direct mouse drag events
  to a consistent control.
* Key events are directed to the focus.
* Tab and enter will change focus to the next control, shift plus these will
  step backward.
"""

import pyglet
from pyglet import gl

import graphics
import layout

from widget import Widget, Container

class Panel(Container):
    """
    Not really a layout element, the panel is a decorative border and
    background for the dialog's elements.
    """

    def __init__(self, content=None):
        Container.__init__(self, content)
        self.panel = None

    def delete(self):
        Container.delete(self)
        if self.panel is not None:
            self.panel.delete()

    def layout(self, x, y):
        self.x, self.y = x, y
        left, right, top, bottom = self.panel.get_margins()
        self.panel.update(x, y, self.width, self.height)
        self.content.layout(x + left, y + bottom)

    def size(self, dialog):
        self.content.size(dialog)
        if self.panel is None:
            self.panel = dialog.get_provider().get_panel(
                dialog.batch, dialog.panel_group,
                color=dialog.stylesheet.color)
        left, right, top, bottom = self.panel.get_margins()
        self.width = self.content.width + left + right
        self.height = self.content.height + top + bottom

class DialogGroup(pyglet.graphics.Group):
    """Ensure that all GUI elements within a dialog can be drawn with
    blending enabled."""
    def set_state(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        gl.glPopAttrib()

class Dialog(Container, pyglet.event.EventDispatcher):
    """
    Defines a new GUI.  By default it can contain only one element, but that
    element can be a Layout of some kind which can contain multiple elements.
    Pass a GraphicProvider in to set the graphic appearance of its elements,
    and a Stylesheet to control the appearance of its text.

    The Dialog is always repositioned in relationship to the screen, and
    handles resize events accordingly.

    You may set callback events for 'on_enter' (handles the case when the
    last field or control element has been iterated from) and 'on_escape'
    (handles the case when escape is pressed).

    Also, you may call 'get_values()' to get the values set by any
    controls in the dialog which have their IDs set.  This can be a convenient
    way to access all elements of a form when the user submits it.
    """
    def __init__(self, content=None, window=None, batch=None, group=None,
                 anchor=layout.ANCHOR_CENTER, offset=(0, 0),
                 provider=graphics.GetDefaultGraphicElementProvider(),
                 stylesheet=graphics.GetDefaultStylesheet(),
                 on_enter=None, on_escape=None):
        """
        Creates a new dialog.
        """
        pyglet.event.EventDispatcher.__init__(self)
        Container.__init__(self, content=content)

        self.window = window
        self.anchor = anchor
        self.offset = offset
        self.provider = provider
        self.stylesheet = stylesheet
        self.on_enter = on_enter
        self.on_escape = on_escape
        if batch is None:
            self.batch = pyglet.graphics.Batch()
            self.own_batch = True
        else:
            self.batch = batch
            self.own_batch = False
        self.root_group = DialogGroup(parent=group)
        self.panel_group = pyglet.graphics.OrderedGroup(0, self.root_group)
        self.bg_group = pyglet.graphics.OrderedGroup(1, self.root_group)
        self.fg_group = pyglet.graphics.OrderedGroup(2, self.root_group)
        self.highlight_group = pyglet.graphics.OrderedGroup(3, self.root_group)
        self.screen = Widget()  # We'll set the dimensions from on_resize
        self.needs_layout = True
        self.controls = []
        self.hover = None
        self.focus = None
        self.values = {}
        self.updatables = []

    def _get_controls(self):
        """
        We iterate through our contents to get only the elements which
        can accept input events.
        """
        return self.content._get_controls()

    def _set_value(self, id, value):
        self.values[id] = value

    def add_updatable(self, updatable):
        """
        We only update contents which have requested update.
        """
        self.updatables.append(updatable)

    def remove_updatable(self, updatable):
        self.updatables.remove(updatable)

    def do_layout(self):
        # Determine size of all components
        self.size(self)

        # We anchor the same corner to the parent as the parent's corner given,
        # so our center is matched to the screen's center, or our top left
        # corner is matched to the screen's top left corner
        self.layout(*layout.GetRelativePoint(self.screen, self.anchor,
                                             self, None, self.offset))
        self.controls = self._get_controls()

        self.needs_layout = False

    def get_provider(self):
        return self.provider

    def get_value(self, id):
        return self.values.get(id)

    def get_values(self):
        return self.values

    def on_key_press(self, symbol, modifiers):
        if symbol in [pyglet.window.key.TAB, pyglet.window.key.ENTER]:
            if not self.controls:
                return

            if modifiers & pyglet.window.key.MOD_SHIFT:
                dir = -1
            else:
                dir = 1

            if self.focus is not None:
                index = self.controls.index(self.focus)
            else:
                index = 0 - dir

            # If we're on the last
            if self.on_enter is not None and \
               dir > 0 and (index + dir) == len(self.controls) and \
               symbol == pyglet.window.key.ENTER:
                self.on_enter(self)

            new_focus = self.controls[(index + dir) % len(self.controls)]
            self.set_focus(new_focus)
            return pyglet.event.EVENT_HANDLED
        elif symbol == pyglet.window.key.ESCAPE and self.on_escape is not None:
            self.on_escape(self)
            return pyglet.event.EVENT_HANDLED
        else:
            if self.focus is not None:
                self.focus.dispatch_event('on_key_press',
                                          self, symbol, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.hover is not None:
            if self.hover.hit_test(x, y):
                self.set_cursor(self.hover.get_cursor(x, y))
                self.hover.dispatch_event('on_mouse_motion',
                                          self, x, y, dx, dy)
                return # no change!
        for control in self.controls:
            if control.hit_test(x, y):
                self.set_hover(control)
                self.set_cursor(self.hover.get_cursor(x, y))
                self.hover.dispatch_event('on_mouse_motion',
                                          self, x, y, dx, dy)
                return pyglet.event.EVENT_HANDLED
        self.set_hover(None)
        self.set_cursor(None)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.focus is not self.hover:
            self.set_focus(self.hover)
        if self.focus is not None:
            return self.focus.dispatch_event(
                'on_mouse_press', self, x, y, button, modifiers)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if self.focus is not None:
            retval = self.focus.dispatch_event(
                'on_mouse_release', self, x, y, buttons, modifiers)
            self.on_mouse_motion(x, y, 0, 0)  # in case we were dragged off
            return retval

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_drag',
                self, x, y, dx, dy, buttons, modifiers)

    def on_text(self, text):
        if self.focus and text != u'\r':
            self.focus.dispatch_event('on_text', self, text)

    def on_text_motion(self, motion):
        if self.focus:
            self.focus.dispatch_event('on_text_motion', self, motion)

    def on_text_motion_select(self, motion):
        if self.focus:
            self.focus.dispatch_event('on_text_motion_select', self, motion)

    def on_update(self, dt):
        if self.needs_layout:
            self.do_layout()
        for updatable in self.updatables:
            updatable.on_update(self, dt)

    def on_resize(self, width, height):
        if self.screen.width != width or self.screen.height != height:
            self.screen.width, self.screen.height = width, height
            self.needs_layout = True

    def set_cursor(self, cursor):
        if cursor is None:
            self.window.set_mouse_cursor(cursor)
        else:
            self.window.set_mouse_cursor(
                self.window.get_system_mouse_cursor(cursor))

    def set_focus(self, focus):
        if self.focus == focus:
            return

        if self.focus is not None:
            self.focus.dispatch_event('on_lose_focus', self)
        self.focus = focus
        if focus is not None:
            focus.dispatch_event('on_gain_focus', self)

    def set_hover(self, hover):
        if self.hover == hover:
            return

        if self.hover is not None:
            self.hover.dispatch_event('on_lose_highlight', self)
        self.hover = hover
        if hover is not None:
            hover.dispatch_event('on_gain_highlight', self)

