# kytten/scrollbar.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control

class HScrollbar(Control):
    """
    A horizontal scrollbar.  Position is measured from 0.0 to 1.0, and bar
    size is set as a percentage of the maximum.
    """
    IMAGE_LEFT = ['hscrollbar', 'left']
    IMAGE_SPACE = ['hscrollbar', 'space']
    IMAGE_BAR = ['hscrollbar', 'bar']
    IMAGE_RIGHT = ['hscrollbar', 'right']
    IMAGE_LEFTMAX = ['hscrollbar', 'leftmax']
    IMAGE_RIGHTMAX = ['hscrollbar', 'rightmax']

    def __init__(self, width):
        """
        Creates a new scrollbar.

        @param width Width of the area for which we are a scrollbar
        """
        Control.__init__(self, width=width, height=0)
        self.__init2__(width)

    def __init2__(self, width):
        """
        HScrollbar and VScrollbar share similiar data structures, which this
        function initializes.

        @param width Width of the area for which we are a scrollbar
        """
        self.left = None
        self.space = None
        self.right = None
        self.bar = None
        self.pos = 0.0
        self.bar_width = 0.5
        self.is_dragging = False
        self.is_scrolling = False
        self.scroll_delta = 0

    def _get_left_region(self):
        """
        Return area of the left button (x, y, width, height)
        """
        if self.left is not None:
            return self.x, self.y, self.left.width, self.height
        else:
            return self.x, self.y, 0, 0

    def _get_right_region(self):
        """
        Return area of the right button (x, y, width, height)
        """
        if self.right is not None:
            return (self.x + self.width - self.right.width, self.y,
                    self.right.width, self.height)
        else:
            return self.x + self.width, self.y, 0, 0

    def _get_space_region(self):
        """
        Return area of the space in which the bar moves
        (x, y, width, height)
        """
        if self.left is not None and self.right is not None:
            return (self.x + self.left.width, self.y,
                    self.width - self.left.width - self.right.width,
                    self.height)
        else:
            return self.x, self.y, self.width, self.height

    def _get_bar_region(self):
        """
        Return area of the bar within the scrollbar (x, y, width, height)
        """
        if self.left is not None and self.right is not None:
            left_width = self.left.width
            right_width = self.right.width
        else:
            left_width = right_width = 0
        self.pos = max(min(self.pos, 1.0 - self.bar_width), 0.0)
        space_width = self.width - left_width - right_width
        return (int(self.x + left_width + self.pos * space_width),
                self.y,
                int(self.bar_width * space_width),
                self.height)

    def delete(self):
        """
        Delete all graphic elements used by the scrollbar
        """
        if self.left is not None:
            self.left.delete()
            self.left = None
        if self.space is not None:
            self.space.delete()
            self.space = None
        if self.bar is not None:
            self.bar.delete()
            self.bar = None
        if self.right is not None:
            self.right.delete()
            self.right = None

    def drag_bar(self, dx, dy):
        """
        Drag the bar, keeping it within limits

        @param dx Delta X
        @param dy Delta Y
        """
        _, _, space_width, space_height = self._get_space_region()
        _, _, bar_width, bar_height = self._get_bar_region()
        self.pos = min(max(self.pos + float(dx) / space_width, 0.0),
                       1.0 - float(bar_width)/space_width)

    def ensure_visible(self, left, right, max_width):
        """
        Ensure that the area of space between left and right is completely
        visible.

        @param left Left end of the space
        @param right Right end of the space
        @param max_width Maximum width of space
        """
        pos_x = self.pos * max_width
        pos_width = self.bar_width * max_width
        if pos_x <= left and pos_x + pos_width > right:
            return  # We're fine
        elif pos_x > left:
            self.pos = pos_x / max_width  # Shift to the left
        elif pos_x + pos_width < right:
            self.pos = (right - pos_width) / max_width  # Shift to the right
        self.pos = min(max(self.pos, 0.0), 1.0 - self.bar_width)
        self.delete()
        self.saved_dialog.set_needs_layout()

    def get(self, width, max_width):
        """
        Returns the position of the bar, in pixels from the controlled area's
        left edge
        """
        return int(self.pos * max_width)

    def layout(self, x, y):
        """
        Lays out the scrollbar components

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        self.x, self.y = x, y
        if self.left is not None:
            self.left.update(*self._get_left_region())
        if self.right is not None:
            self.right.update(*self._get_right_region())
        if self.space is not None:
            self.space.update(*self._get_space_region())
        if self.bar is not None:
            self.bar.update(*self._get_bar_region())

    def on_gain_focus(self):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_target(self)

    def on_lose_focus(self):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_target(None)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """
        We drag the bar only if the user had previously clicked on the bar

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param dx Delta X
        @param dy Delta Y
        @param buttons Buttons held while dragging
        @param modifiers Modifiers to apply to buttons
        """
        if self.is_dragging:
            self.drag_bar(dx, dy)
            self.delete()
            self.saved_dialog.set_needs_layout()
            return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        """
        If the mouse press falls within the space, move the bar over to the
        mouse.  Otherwise, activate scrolling.

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button being pressed
        @param modifiers Modifiers to apply to button
        """
        space_x, space_y, space_width, space_height = self._get_space_region()
        if x >= space_x and x < space_x + space_width and \
           y >= space_y and y < space_y + space_height:
            self.set_bar_pos(x, y)
            self.is_dragging = True
            self.delete()
            self.saved_dialog.set_needs_layout()
        else:
            left_x, left_y, left_width, left_height = self._get_left_region()
            if x >= left_x and x < left_x + left_width and \
               y >= left_y and y < left_y + left_height:
                self.is_scrolling = True
                self.scroll_delta = -1
            else:
                right_x, right_y, right_width, right_height = \
                       self._get_right_region()
                if x >= right_x and x < right_x + right_width and \
                   y >= right_y and y < right_y + right_height:
                    self.is_scrolling = True
                    self.scroll_delta = 1

    def on_mouse_release(self, x, y, button, modifiers):
        """
        Cancels dragging or scrolling

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button being released
        @param modifiers Modifiers to apply to button
        """
        self.is_dragging = False
        self.is_scrolling = False
        self.scroll_delta = 0

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """
        Mousewheel was moved some number of clicks

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param scroll_x Number of clicks horizontally mouse was moved
        @param scroll_y Number of clicks vertically mouse was moved
        """
        self.drag_bar(scroll_y * 10, 0)
        self.delete()
        self.saved_dialog.set_needs_layout()

    def on_update(self, dt):
        """
        When scrolling, we increment our position each update

        @param dt Time delta, in seconds
        """
        if self.is_scrolling:
            self.drag_bar(self.scroll_delta * 50.0 * dt, 0)
            self.saved_dialog.set_needs_layout()

    def set(self, width, max_width):
        """
        Sets the width of the scrollbar

        @param width Width the scrollbar occupies
        @param max_width Maximum width of the scrollable area
        """
        self.width = width
        self.bar_width = max(float(width) / max_width, 0.0)
        self.pos = min(self.pos, 1.0 - self.bar_width)

    def set_bar_pos(self, x, y):
        """
        When the mouse is pressed within scrollbar space, move the bar over
        underneath it.

        @param x X coordinate of mouse press
        @param y Y coordinate of mouse press
        """
        space_x, space_y, space_width, space_height = self._get_space_region()
        bar_x, bar_y, bar_width, bar_height = self._get_bar_region()
        if x < bar_x:
            self.pos = float(x - space_x) / space_width
        elif x > bar_x + bar_width:
            max_bar_x = space_width - bar_width
            x -= bar_width
            self.pos = float(min(max_bar_x, x - space_x)) / space_width
        if self.bar is not None:
            self.bar.update(*self._get_bar_region())

    def size(self, dialog):
        """
        Creates scrollbar components.
        """
        if dialog is None:
            return
        Control.size(self, dialog)
        dialog.set_wheel_hint(self)
        if self.left is None:
            if self.pos > 0.0:
                path = self.IMAGE_LEFT
            else:
                path = self.IMAGE_LEFTMAX
            self.left = dialog.theme[path]['image'].generate(
                dialog.theme[path]['gui_color'],
                dialog.batch, dialog.fg_group)

            # Left button is our basis for minimum dimension
            self.width, self.height = self.left.width, self.left.height
        if self.space is None:
            path = self.IMAGE_SPACE
            self.space = dialog.theme[path]['image'].generate(
                dialog.theme[path]['gui_color'],
                dialog.batch, dialog.fg_group)
        if self.bar is None:
            path = self.IMAGE_BAR
            self.bar = dialog.theme[path]['image'].generate(
                dialog.theme[path]['gui_color'],
                dialog.batch, dialog.fg_group)
        if self.right is None:
            if self.pos < 1.0 - self.bar_width:
                path = self.IMAGE_RIGHT
            else:
                path = self.IMAGE_RIGHTMAX
            self.right = dialog.theme[path]['image'].generate(
                dialog.theme[path]['gui_color'],
                dialog.batch, dialog.fg_group)

class VScrollbar(HScrollbar):
    """
    A vertical scrollbar.  Position is measured from 0.0 to 1.0, and bar size
    is set as a percentage of the maximum.  Note that left is top, and
    right is bottom, from the viewpoint of the VScrollbar.
    """
    IMAGE_LEFT = ['vscrollbar', 'up']
    IMAGE_SPACE = ['vscrollbar', 'space']
    IMAGE_BAR = ['vscrollbar', 'bar']
    IMAGE_RIGHT = ['vscrollbar', 'down']
    IMAGE_LEFTMAX = ['vscrollbar', 'upmax']
    IMAGE_RIGHTMAX = ['vscrollbar', 'downmax']

    def __init__(self, height):
        """
        Creates a new scrollbar.  At the outset, we are presented with maximum
        height and the templates to use.

        @param height Height of the area for which we are a scrollbar
        """
        Control.__init__(self, width=0, height=height)
        self.__init2__(height)

    def _get_left_region(self):
        """Returns the area occupied by the up button
        (x, y, width, height)"""
        if self.left is not None:
            return (self.x, self.y + self.height - self.left.height,
                    self.width, self.left.height)
        else:
            return self.x, self.y, 0, 0

    def _get_right_region(self):
        """Returns the area occupied by the down button
        (x, y, width, height)"""
        if self.right is not None:
            return self.x, self.y, self.width, self.right.height
        else:
            return self.x, self.y, 0, 0

    def _get_space_region(self):
        """Returns the area occupied by the space between up and down
        buttons (x, y, width, height)"""
        if self.left is not None and self.right is not None:
            return (self.x,
                    self.y + self.right.height,
                    self.width,
                    self.height - self.left.width - self.right.width)
        else:
            return self.x, self.y, self.width, self.height

    def _get_bar_region(self):
        """Returns the area occupied by the bar (x, y, width, height)"""
        if self.left is not None and self.right is not None:
            left_height = self.left.height
            right_height = self.right.height
        else:
            left_height = right_height = 0
        self.pos = max(min(self.pos, 1.0 - self.bar_width), 0.0)
        space_height = self.height - left_height - right_height
        top = self.y + self.height - left_height
        return (self.x, int(top - (self.pos + self.bar_width) * space_height),
                self.width, int(self.bar_width * space_height))

    def drag_bar(self, dx, dy):
        """Handles dragging the bar.

        @param dx Delta X
        @param dy Delta Y
        """
        _, _, space_width, space_height = self._get_space_region()
        _, _, bar_width, bar_height = self._get_bar_region()
        self.pos = min(max(self.pos - float(dy) / space_height, 0.0),
                       1.0 - float(bar_height)/space_height)

    def ensure_visible(self, top, bottom, max_height):
        """
        Ensure that the area of space between top and bottom is completely
        visible.

        @param top Top end of the space
        @param bottom Bottom end of the space
        @param max_height Maximum height of space
        """
        bar_top = (1.0 - self.pos) * max_height
        bar_bottom = bar_top - self.bar_width * max_height
        if bar_top > top and bar_bottom <= bottom:
            return  # We're fine
        elif bar_top < top:
            # Shift upward
            self.pos = 1.0 - float(top) / max_height
        elif bar_bottom > bottom:
            # Shift downward
            self.pos = 1.0 - float(bottom) / max_height - self.bar_width
        self.pos = min(max(self.pos, 0.0), 1.0 - self.bar_width)
        self.delete()
        self.saved_dialog.set_needs_layout()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """
        Mousewheel was moved some number of clicks

        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param scroll_x Number of clicks horizontally mouse was moved
        @param scroll_y Number of clicks vertically mouse was moved
        """
        self.drag_bar(0, scroll_y * 10)
        self.delete()
        self.saved_dialog.set_needs_layout()

    def on_update(self, dt):
        """
        When scrolling, we increment our position each update

        @param dialog Dialog in which we're contained
        @param dt Time delta, in seconds
        """
        if self.is_scrolling:
            self.drag_bar(0, -self.scroll_delta * 50.0 * dt)
            self.saved_dialog.set_needs_layout()

    def set(self, height, max_height):
        """Sets the new height of the scrollbar, and the height of
        the bar relative to the scrollable area.

        @param height Scrollable region height
        @param max_height Maximum scrollable height
        """
        self.height = height
        self.bar_width = max(float(height) / max_height, 0.0)
        self.pos = min(self.pos, 1.0 - self.bar_width)

    def set_bar_pos(self, x, y):
        """Sets the scrollbar position.  Moves the scrollbar to intercept
        the mouse if it is not already in place."""
        space_x, space_y, space_width, space_height = self._get_space_region()
        bar_x, bar_y, bar_width, bar_height = self._get_bar_region()
        top = space_y + space_height
        if y > bar_y + bar_height:
            self.pos = float(top - y) / space_height
        elif y < bar_y:
            y += bar_height
            max_bar_y = space_height - bar_height
            self.pos = float(min(max_bar_y, top - y)) / space_height
        if self.bar is not None:
            self.bar.update(*self._get_bar_region())

