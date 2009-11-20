# kytten/dialog.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

from widgets import Widget, Control, Label
from button import Button
from frame import Wrapper, Frame
from layout import GetRelativePoint, ANCHOR_CENTER
from layout import VerticalLayout, HorizontalLayout

class DialogEventManager(Control):
    def __init__(self):
        """
        Creates a new event manager for a dialog.

        @param content The Widget which we wrap
        """
        Control.__init__(self)
        self.controls = []
        self.control_areas = {}
        self.control_map = {}
        self.hover = None
        self.focus = None
        self.wheel_hint = None
        self.wheel_target = None

    def get_value(self, id):
        widget = self.get_widget(id)
        if widget is not None:
            return widget.get_value()

    def get_values(self):
        retval = {}
        for widget in self.controls:
            if widget.is_input() and widget.id is not None:
                retval[widget.id] = widget.get_value()
        return retval

    def get_widget(self, id):
        return self.control_map.get(id)

    def hit_control(self, x, y, control):
        left, right, top, bottom = self.control_areas[control]
        if x >= left and x < right and y >= bottom and y < top:
            return control.hit_test(x, y)
        else:
            return False

    def on_key_press(self, symbol, modifiers):
        """
        TAB and ENTER will move us between fields, holding shift will
        reverse the direction of our iteration.  We don't handle ESCAPE.
        Otherwise, we pass keys to our child elements.

        @param symbol Key pressed
        @param modifiers Modifiers for key press
        """
        if symbol in [pyglet.window.key.TAB, pyglet.window.key.ENTER]:
            focusable = [x for x in self.controls
                         if x.is_focusable() and not x.is_disabled()]
            if not focusable:
                return

            if modifiers & pyglet.window.key.MOD_SHIFT:
                dir = -1
            else:
                dir = 1

            if self.focus is not None and self.focus in focusable:
                index = focusable.index(self.focus)
            else:
                index = 0 - dir

            new_focus = focusable[(index + dir) % len(focusable)]
            self.set_focus(new_focus)
            new_focus.ensure_visible()

            # If we hit ENTER, and wrapped back to the first focusable,
            # pass the ENTER back so the Dialog can call its on_enter callback
            if symbol != pyglet.window.key.ENTER or \
               new_focus != focusable[0]:
                return pyglet.event.EVENT_HANDLED

        elif symbol != pyglet.window.key.ESCAPE:
            if self.focus is not None and hasattr(self.focus, 'on_key_press'):
                return self.focus.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        """Pass key release events to the focus

        @param symbol Key released
        @param modifiers Modifiers for key released
        """
        if self.focus is not None and hasattr(self.focus, 'on_key_release'):
            return self.focus.on_key_release(symbol, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """
        Handles mouse dragging.  If we have a focus, pass it in.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        @param buttons Buttons held while moving
        @param modifiers Modifiers to apply to buttons
        """
        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_drag',
                                      x, y, dx, dy, buttons, modifiers)
            return pyglet.event.EVENT_HANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        """
        Handles mouse motion.  We highlight controls that we are hovering
        over.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        """
        if self.hover is not None and not self.hit_control(x, y, self.hover):
            self.hover.dispatch_event('on_mouse_motion', x, y, dx, dy)
        new_hover = None
        for control in self.controls:
            if self.hit_control(x, y, control):
                new_hover = control
                break
        self.set_hover(new_hover)
        if self.hover is not None:
            self.hover.dispatch_event('on_mouse_motion', x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        """
        If the focus is set, and the target lies within the focus, pass the
        message down.  Otherwise, check if we need to assign a new focus.
        If the mouse was pressed within our frame but no control was targeted,
        we may be setting up to drag the Dialog around.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        """
        if self.focus is not None and self.hit_control(x, y, self.focus):
            self.focus.dispatch_event('on_mouse_press',
                                      x, y, button, modifiers)
            return pyglet.event.EVENT_HANDLED
        else:
            if self.hit_test(x, y):
                self.set_focus(self.hover)
                if self.focus is not None:
                    self.focus.dispatch_event('on_mouse_press',
                                              x, y, button, modifiers)
                    return pyglet.event.EVENT_HANDLED
            else:
                self.set_focus(None)

    def on_mouse_release(self, x, y, button, modifiers):
        """
        Button was released.  We pass this along to the focus, then we
        generate an on_mouse_motion to handle changing the highlighted
        Control if necessary.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button released
        @param modifiers Modifiers to apply to button
        """
        self.is_dragging = False
        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_release',
                                      x, y, button, modifiers)
        DialogEventManager.on_mouse_motion(self, x, y, 0, 0)
        return pyglet.event.EVENT_HANDLED

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """
        Mousewheel was scrolled.  See if we have a wheel target, or
        failing that, a wheel hint.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param scroll_x Number of clicks horizontally mouse was moved
        @param scroll_y Number of clicks vertically mouse was moved
        """
        if self.wheel_target is not None and \
           self.wheel_target in self.controls:
            self.wheel_target.dispatch_event('on_mouse_scroll',
                                             x, y, scroll_x, scroll_y)
            return pyglet.event.EVENT_HANDLED
        elif self.wheel_hint is not None and \
             self.wheel_hint in self.controls:
            self.wheel_hint.dispatch_event('on_mouse_scroll',
                                           x, y, scroll_x, scroll_y)
            return pyglet.event.EVENT_HANDLED

    def on_text(self, text):
        if self.focus and text != u'\r':
            try:
                return getattr(self.focus, 'on_text')(text)
            except KeyError:
                return pyglet.event.EVENT_UNHANDLED

    def on_text_motion(self, motion):
        if self.focus:
            try:
                return getattr(self.focus, 'on_text_motion')(motion)
            except KeyError:
                return pyglet.event.EVENT_UNHANDLED

    def on_text_motion_select(self, motion):
        if self.focus:
            try:
                return getattr(self.focus, 'on_text_motion_select')(motion)
            except KeyError:
                return pyglet.event.EVENT_UNHANDLED

    def on_update(self, dt):
        """
        We update our layout only when it's time to construct another frame.
        Since we may receive several resize events within this time, this
        ensures we don't resize too often.

        @param dialog The Dialog containing the controls
        @param dt Time passed since last update event (in seconds)
        """
        for control in self.controls:
            control.dispatch_event('on_update', dt)

    def set_focus(self, focus):
        """
        Sets a new focus, dispatching lose and gain focus events appropriately

        @param focus The new focus, or None if no focus
        """
        if self.focus == focus:
            return
        if self.focus is not None:
            self.focus.dispatch_event('on_lose_focus')
        self.focus = focus
        if focus is not None:
            focus.dispatch_event('on_gain_focus')

    def set_hover(self, hover):
        """
        Sets a new highlight, dispatching lose and gain highlight events
        appropriately

        @param hover The new highlight, or None if no highlight
        """
        if self.hover == hover:
            return
        if self.hover is not None:
            self.hover.dispatch_event('on_lose_highlight')
        self.hover = hover
        if hover is not None:
            hover.dispatch_event('on_gain_highlight')

    def set_wheel_hint(self, control):
        self.wheel_hint = control

    def set_wheel_target(self, control):
        self.wheel_target = control

    def teardown(self):
        self.controls = []
        self.control_map = {}
        self.focus = None
        self.hover = None
        self.wheel_hint = None
        self.wheel_target = None

    def update_controls(self):
        """Update our list of controls which may respond to user input."""
        controls = self._get_controls()
        self.controls = []
        self.control_areas = {}
        self.control_map = {}
        for control, left, right, top, bottom in controls:
            self.controls.append(control)
            self.control_areas[control] = (left, right, top, bottom)
            if control.id is not None:
                self.control_map[control.id] = control

        if self.hover is not None and self.hover not in self.controls:
            self.set_hover(None)
        if self.focus is not None and self.focus not in self.controls:
            self.set_focus(None)

kytten_next_dialog_order_id = 0
def GetNextDialogOrderId():
    global kytten_next_dialog_order_id
    kytten_next_dialog_order_id += 1
    return kytten_next_dialog_order_id

class DialogGroup(pyglet.graphics.OrderedGroup):
    """
    Ensure that all Widgets within a Dialog can be drawn with
    blending enabled, and that our Dialog will be drawn in a particular
    order relative to other Dialogs.
    """
    def __init__(self, parent=None):
        """
        Creates a new DialogGroup.  By default we'll be on top.

        @param parent Parent group
        """
        pyglet.graphics.OrderedGroup.__init__(
            self, GetNextDialogOrderId(), parent)
        self.real_order = self.order

    def __cmp__(self, other):
        """
        When compared with other DialogGroups, we'll return our real order
        compared against theirs; otherwise use the OrderedGroup comparison.
        """
        if isinstance(other, DialogGroup):
            return cmp(self.real_order, other.real_order)
        else:
            return OrderedGroup.__cmp__(self, other)

    def is_on_top(self):
        """
        Are we the top dialog group?
        """
        global kytten_next_dialog_order_id
        return self.real_order == kytten_next_dialog_order_id

    def pop_to_top(self):
        """
        Put us on top of other dialog groups.
        """
        self.real_order = GetNextDialogOrderId()

    def set_state(self):
        """
        Ensure that blending is set.
        """
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        """
        Restore previous blending state.
        """
        gl.glPopAttrib()

class Dialog(Wrapper, DialogEventManager):
    """
    Defines a new GUI.  By default it can contain only one element, but that
    element can be a Layout of some kind which can contain multiple elements.
    Pass a Theme in to set the graphic appearance of the Dialog.

    The Dialog is always repositioned in relationship to the window, and
    handles resize events accordingly.
    """
    def __init__(self, content=None, window=None, batch=None, group=None,
                 anchor=ANCHOR_CENTER, offset=(0, 0), parent=None,
                 theme=None, movable=True, on_enter=None, on_escape=None):
        """
        Creates a new dialog.

        @param content The Widget which we wrap
        @param window The window to which we belong; used to set the
                      mouse cursor when appropriate.  If set, we will
                      add ourself to the window as a handler.
        @param batch Batch in which we are to place our graphic elements;
                     may be None if we are to create our own Batch
        @param group Group in which we are to place our graphic elements;
                     may be None
        @param anchor Anchor point of the window, relative to which we
                      are positioned.  If ANCHOR_TOP_LEFT is specified,
                      our top left corner will be aligned to the window's
                      top left corner; if ANCHOR_CENTER is specified,
                      our center will be aligned to the window's center,
                      and so forth.
        @param offset Offset from the anchor point.  A positive X is always
                      to the right, a positive Y to the upward direction.
        @param theme The Theme which we are to use to generate our graphical
                     appearance.
        @param movable True if the dialog is able to be moved
        @param on_enter Callback for when user presses enter on the last
                        input within this dialog, i.e. form submit
        @param on_escape Callback for when user presses escape
        """
        assert isinstance(theme, dict)
        Wrapper.__init__(self, content=content)
        DialogEventManager.__init__(self)

        self.window = window
        self.anchor = anchor
        self.offset = offset
        self.theme = theme
        self.is_movable = movable
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
        self.needs_layout = True
        self.is_dragging = False

        if window is None:
            self.screen = Widget()
        else:
            width, height = window.get_size()
            self.screen = Widget(width=width, height=height)
            window.push_handlers(self)

    def do_layout(self):
        """
        We lay out the Dialog by first determining the size of all its
        chlid Widgets, then laying ourself out relative to the parent window.
        """
        # Determine size of all components
        self.size(self)

        # Calculate our position relative to our containing window,
        # making sure that we fit completely on the window.  If our offset
        # would send us off the screen, constrain it.
        x, y = GetRelativePoint(self.screen, self.anchor,
                                self, None, (0, 0))
        max_offset_x = self.screen.width - self.width - x
        max_offset_y = self.screen.height - self.height - y
        offset_x, offset_y = self.offset
        offset_x = max(min(offset_x, max_offset_x), -x)
        offset_y = max(min(offset_y, max_offset_y), -y)
        self.offset = (offset_x, offset_y)
        x += offset_x
        y += offset_y

        # Perform the actual layout now!
        self.layout(x, y)
        self.update_controls()

        self.needs_layout = False

    def draw(self):
        assert self.own_batch
        self.batch.draw()

    def ensure_visible(self, control):
        """
        Ensure a control is visible.  For Dialog, this doesn't matter
        since we don't scroll.
        """
        pass

    def get_root(self):
        return self

    def on_key_press(self, symbol, modifiers):
        """
        We intercept TAB, ENTER, and ESCAPE events.  TAB and ENTER will
        move us between fields, holding shift will reverse the direction
        of our iteration.  ESCAPE may cause us to send an on_escape
        callback.

        Otherwise, we pass key presses to our child elements.

        @param symbol Key pressed
        @param modifiers Modifiers for key press
        """
        retval = DialogEventManager.on_key_press(self, symbol, modifiers)
        if not retval:
            if symbol in [pyglet.window.key.TAB, pyglet.window.key.ENTER]:
                if self.on_enter is not None:
                    self.on_enter(self)
                    return pyglet.event.EVENT_HANDLED
            elif symbol == pyglet.window.key.ESCAPE:
                if self.on_escape is not None:
                    self.on_escape(self)
                    return pyglet.event.EVENT_HANDLED
        return retval

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """
        Handles mouse dragging.  If we have a focus, pass it in.  Otherwise
        if we are movable, and we were being dragged, move the window.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        @param buttons Buttons held while moving
        @param modifiers Modifiers to apply to buttons
        """
        if not DialogEventManager.on_mouse_drag(self, x, y, dx, dy,
                                                buttons, modifiers):
            if self.is_movable and self.is_dragging:
                x, y = self.offset
                self.offset = (int(x + dx), int(y + dy))
                self.set_needs_layout()
                return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        """
        If the focus is set, and the target lies within the focus, pass the
        message down.  Otherwise, check if we need to assign a new focus.
        If the mouse was pressed within our frame but no control was targeted,
        we may be setting up to drag the Dialog around.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button pressed
        @param modifiers Modifiers to apply to button
        """
        retval = DialogEventManager.on_mouse_press(self, x, y,
                                             button, modifiers)
        if self.hit_test(x, y):
            if not self.root_group.is_on_top():
                self.pop_to_top()
            if not retval:
                self.is_dragging = True
                retval = pyglet.event.EVENT_HANDLED
        return retval

    def on_mouse_release(self, x, y, button, modifiers):
        """
        Button was released.  We pass this along to the focus, then we
        generate an on_mouse_motion to handle changing the highlighted
        Control if necessary.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button released
        @param modifiers Modifiers to apply to button
        """
        self.is_dragging = False
        return DialogEventManager.on_mouse_release(self, x, y,
                                                   button, modifiers)

    def on_resize(self, width, height):
        """
        Update our knowledge of the window's width and height.

        @param width Width of the window
        @param height Height of the window
        """
        if self.screen.width != width or self.screen.height != height:
            self.screen.width, self.screen.height = width, height
            self.needs_layout = True

    def on_update(self, dt):
        """
        We update our layout only when it's time to construct another frame.
        Since we may receive several resize events within this time, this
        ensures we don't resize too often.

        @param dt Time passed since last update event (in seconds)
        """
        if self.needs_layout:
            self.do_layout()
        DialogEventManager.on_update(self, dt)

    def pop_to_top(self):
        """
        Pop our dialog group to the top, and force our batch to re-sort
        the groups.  Also, puts our event handler on top of the window's
        event handler stack.
        """
        self.root_group.pop_to_top()
        self.batch._draw_list_dirty = True  # forces resorting groups
        if self.window is not None:
            self.window.remove_handlers(self)
            self.window.push_handlers(self)

    def set_needs_layout(self):
        """
        True if we should redo the Dialog layout on our next update.
        """
        self.needs_layout = True

    def teardown(self):
        DialogEventManager.teardown(self)
        if self.content is not None:
            self.content.teardown()
            self.content = None
        if self.window is not None:
            self.window.remove_handlers(self)
            self.window = None
        self.batch._draw_list_dirty = True  # forces resorting groups

class PopupMessage(Dialog):
    """A simple fire-and-forget dialog."""

    def __init__(self, text="", window=None, batch=None, group=None,
                 theme=None, on_escape=None):
        def on_ok(dialog=None):
            if on_escape is not None:
                on_escape(self)
            self.teardown()

        return Dialog.__init__(self, content=Frame(
            VerticalLayout([
                Label(text),
                Button("Ok", on_click=on_ok),
            ])),
            window=window, batch=batch, group=group,
            theme=theme, movable=True,
            on_enter=on_ok, on_escape=on_ok)

class PopupConfirm(Dialog):
    """An ok/cancel-style dialog.  Escape defaults to cancel."""

    def __init__(self, text="", ok="Ok", cancel="Cancel",
                 window=None, batch=None, group=None, theme=None,
                 on_ok=None, on_cancel=None):
        def on_ok_click(dialog=None):
            if on_ok is not None:
                on_ok(self)
            self.teardown()

        def on_cancel_click(dialog=None):
            if on_cancel is not None:
                on_cancel(self)
            self.teardown()

        return Dialog.__init__(self, content=Frame(
            VerticalLayout([
                Label(text),
                HorizontalLayout([
                    Button(ok, on_click=on_ok_click),
                    None,
                    Button(cancel, on_click=on_cancel_click)
                ]),
            ])),
            window=window, batch=batch, group=group,
            theme=theme, movable=True,
            on_enter=on_ok_click, on_escape=on_cancel_click)