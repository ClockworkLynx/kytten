# kytten/slider.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control

class Slider(Control):
    """
    A horizontal slider.  Position is measured from 0.0 to 1.0.
    """
    IMAGE_BAR = ['slider', 'bar']
    IMAGE_KNOB = ['slider', 'knob']
    IMAGE_STEP = ['slider', 'step']

    def __init__(self, value=0.0, min_value=0.0, max_value=1.0, steps=None,
                 width=100, id=None, on_set=None, disabled=False):
        """
        Creates a new slider.

        @param min_value Minimum value
        @param max_value Maximum value
        @param steps None if this slider should cover the range from 0.0 to
                     1.0 smoothly, otherwise we will divide the range
                     up into steps.  For instance, 2 steps would give the
                     possible values 0, 0.5, and 1.0 (then multiplied by scale)
        @param width Minimum width of the tracking area.  Note that this
                     is the interior length of the slider, not the overall
                     size.
        @param id ID for identifying this slider.
        @param on_set Callback function for when the value of this slider
                      changes.
        @param diasbled True if the slider should be disabled
        """
        Control.__init__(self, id=id, disabled=disabled)
        self.min_value = min_value
        self.max_value = max_value
        self.steps = steps
        self.min_width = width
        self.on_set = on_set
        self.bar = None
        self.knob = None
        self.markers = []
        self.pos = max(
            min(float(value - min_value) / (max_value - min_value), 1.0),
            0.0)
        self.offset = (0, 0)
        self.step_offset = (0, 0)
        self.padding = (0, 0, 0, 0)
        self.is_dragging = False

    def delete(self):
        """
        Delete all graphic elements used by the slider
        """
        if self.bar is not None:
            self.bar.delete()
            self.bar = None
        if self.knob is not None:
            self.knob.delete()
            self.knob = None
        for marker in self.markers:
            marker.delete()
        self.markers = []

    def expand(self, width, height):
        self.width = width

    def get_value(self):
        return self.min_value + (self.max_value - self.min_value) * self.pos

    def is_expandable(self):
        return True

    def is_input(self):
        return True

    def layout(self, x, y):
        """
        Lays out the slider components

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        self.x, self.y = x, y
        if self.bar is not None:
            left, right, top, bottom = self.padding
            self.bar.update(x + left, y + bottom,
                            self.width - left - right,
                            self.height - top - bottom)
            x, y, width, height = self.bar.get_content_region()

            if self.knob is not None:
                offset_x, offset_y = self.offset
                self.knob.update(x + int(width * self.pos) + offset_x,
                                 y + offset_y,
                                 self.knob.width, self.knob.height)

            if self.markers:
                step = float(width) / self.steps
                offset_x, offset_y = self.step_offset
                for n in xrange(0, self.steps + 1):
                    self.markers[n].update(int(x + step * n) + offset_x,
                                           y + offset_y,
                                           self.markers[n].width,
                                           self.markers[n].height)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.is_dragging and self.bar is not None:
            bar_x, bar_y, bar_width, bar_height = self.bar.get_content_region()
            self.set_pos(self.pos + float(dx) / bar_width)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.is_disabled():
            return

        self.is_dragging = True
        if self.bar is not None:
            bar_x, bar_y, bar_width, bar_height = self.bar.get_content_region()
            self.set_pos(float(x - bar_x) / bar_width)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.is_disabled():
            return

        self.is_dragging = False
        self.snap_to_nearest()
        if self.on_set is not None:
            value = self.get_value()
            if self.id is not None:
                self.on_set(self.id, value)
            else:
                self.on_set(value)

    def set_pos(self, pos):
        self.pos = max(min(pos, 1.0), 0.0)
        if self.bar is not None and self.knob is not None:
            x, y, width, height = self.bar.get_content_region()
            offset_x, offset_y = self.offset
            self.knob.update(x + int(width * self.pos) + offset_x,
                             y + offset_y,
                             self.knob.width, self.knob.height)

    def size(self, dialog):
        """
        Creates slider components.
        """
        if dialog is None:
            return
        Control.size(self, dialog)
        if self.is_disabled():
            color = dialog.theme['slider']['disabled_color']
        else:
            color = dialog.theme['slider']['gui_color']
        if self.bar is None:
            path = self.IMAGE_BAR
            self.bar = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.bg_group)
            self.padding = dialog.theme[path]['padding']
        if self.knob is None:
            path = self.IMAGE_KNOB
            self.knob = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.highlight_group)
            self.offset = dialog.theme[path]['offset']
        if not self.markers and self.steps is not None:
            path = self.IMAGE_STEP
            for n in xrange(0, self.steps + 1):
                self.markers.append(
                    dialog.theme[path]['image'].generate(
                        color,
                        dialog.batch, dialog.fg_group))
            self.step_offset = dialog.theme[path]['offset']
        width, height = self.bar.get_needed_size(self.min_width, 0)
        left, right, top, bottom = self.padding
        self.width = width + left + right
        self.height = height + top + bottom

    def snap_to_nearest(self):
        if self.steps is not None:
            n = int(self.pos * self.steps + 0.5)
            self.set_pos(float(n) / self.steps)

    def teardown(self):
        self.on_set = None
        Control.teardown(self)