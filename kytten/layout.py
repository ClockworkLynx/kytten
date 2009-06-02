# kytten/layout.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

"""
Layout is controlled here.  In general, we align Dialogs to the screen, or
widgets within a layout, through either VALIGN (vertical align), HALIGN
(horizontal align), or ANCHOR (an anchor point on the screen or the parent
widget).

There are three basic layouts offered here:
* VerticalLayout: elements are lined up from top to bottom
* HorizontalLayout: elements are lined up from left to right
* GridLayout: elements are given in table rows, each containing cells
              in left to right order
"""

import pyglet
from pyglet import gl

VALIGN_TOP = 1
VALIGN_CENTER = 0
VALIGN_BOTTOM = -1

HALIGN_LEFT = -1
HALIGN_CENTER = 0
HALIGN_RIGHT = 1

ANCHOR_TOP_LEFT = (VALIGN_TOP, HALIGN_LEFT)
ANCHOR_TOP = (VALIGN_TOP, HALIGN_CENTER)
ANCHOR_TOP_RIGHT = (VALIGN_TOP, HALIGN_RIGHT)
ANCHOR_LEFT = (VALIGN_CENTER, HALIGN_LEFT)
ANCHOR_CENTER = (VALIGN_CENTER, HALIGN_CENTER)
ANCHOR_RIGHT = (VALIGN_CENTER, HALIGN_RIGHT)
ANCHOR_BOTTOM_LEFT = (VALIGN_BOTTOM, HALIGN_LEFT)
ANCHOR_BOTTOM = (VALIGN_BOTTOM, HALIGN_CENTER)
ANCHOR_RIGHT = (VALIGN_BOTTOM, HALIGN_RIGHT)

from widget import Widget, Container

def GetRelativePoint(parent, parent_anchor, child, child_anchor, offset):
    valign, halign = parent_anchor or ANCHOR_CENTER

    if valign == VALIGN_TOP:
        y = parent.y + parent.height
    elif valign == VALIGN_CENTER:
        y = parent.y + parent.height / 2
    else: # VALIGN_BOTTOM
        y = parent.y

    if halign == HALIGN_LEFT:
        x = parent.x
    elif halign == HALIGN_CENTER:
        x = parent.x + parent.width / 2
    else: # HALIGN_RIGHT
        x = parent.x + parent.width

    valign, halign = child_anchor or (valign, halign)
    offset_x, offset_y = offset

    if valign == VALIGN_TOP:
        y += offset_y - child.height
    elif valign == VALIGN_CENTER:
        y += offset_y - child.height/2
    else: # VALIGN_BOTTOM
        y += offset_y

    if halign == HALIGN_LEFT:
        x += offset_x
    elif halign == HALIGN_CENTER:
        x += offset_x - child.width / 2
    else: # HALIGN_RIGHT
        x += offset_x - child.width

    return (x, y)

class VerticalLayout(Widget):
    """
    A vertical stack of widgets.  Objects are sorted top to bottom.
    """
    def __init__(self, content=[], align=HALIGN_CENTER, padding=5):
        assert isinstance(content, list) or isinstance(content, tuple)
        Widget.__init__(self)
        self.align = align
        self.padding = padding
        self.content = list(content)
        self.dialog = None

    def _get_controls(self):
        controls = []
        for item in self.content:
            controls += item._get_controls()
        return controls

    def add_item(self, item):
        self.content.append(item)
        if self.dialog is not None:
            self.dialog.needs_layout = True

    def delete(self):
        for item in self.content:
            item.delete()
        Widget.delete(self)

    def remove_item(self, content):
        self.content.remove(item)
        if self.dialog is not None:
            self.dialog.needs_layout = True

    def size(self, dialog):
        height = self.padding
        width = 2 * self.padding
        for item in self.content:
            item.size(dialog)
            height += item.height + self.padding
            width = max(width, item.width + 2 * self.padding)
        self.width, self.height = width, height

    def layout(self, x, y):
        Widget.layout(self, x, y)
        top = y + self.height - self.padding
        if self.align == HALIGN_RIGHT:
            for item in self.content:
                item.layout(x + self.width - item.width - self.padding,
                            top - item.height)
                top -= item.height + self.padding
        elif self.align == HALIGN_CENTER:
            for item in self.content:
                item.layout(x + self.width/2 - item.width/2,
                            top - item.height)
                top -= item.height + self.padding
        else: # HALIGN_LEFT
            for item in self.content:
                item.layout(x + self.padding, top - item.height)
                top -= item.height + self.padding

class HorizontalLayout(VerticalLayout):
    """
    A horizontal row of widgets.  Objects are sorted left to right.
    """
    def __init__(self, content=[], align=VALIGN_CENTER, padding=5):
        VerticalLayout.__init__(self, content, align, padding)
        assert isinstance(content, list) or isinstance(content, tuple)

    def size(self, dialog):
        height = 2 * self.padding
        width = self.padding
        for item in self.content:
            item.size(dialog)
            height = max(height, item.height + 2 * self.padding)
            width += item.width + self.padding
        self.width, self.height = width, height

    def layout(self, x, y):
        Widget.layout(self, x, y)
        left = x
        if self.align == VALIGN_TOP:
            for item in self.content:
                item.layout(left,
                            y + self.height - item.height - self.padding)
                left += item.width + self.padding
        elif self.align == VALIGN_CENTER:
            for item in self.content:
                item.layout(left,
                            y + self.height/2 - item.height/2)
                left += item.width + self.padding
        else: # VALIGN_BOTTOM
            for item in self.content:
                item.layout(left, y + self.padding)
                left += item.width + self.padding

class GridLayout(VerticalLayout):
    """
    A grid of widgets.  Content is given in rows of objects.  The GridLayout
    takes an overall anchor which specifies how objects should be aligned
    within cells; by default they are aligned to the top left corner of
    each cell.
    """
    def __init__(self, content=[[]], anchor=ANCHOR_TOP_LEFT, padding=5,
                 offset=(0, 0)):
        VerticalLayout.__init__(self, content, anchor, padding)
        assert ((isinstance(content, list) or
                 isinstance(content, tuple)) and
                (isinstance(content[0], list) or
                 isinstance(content[0], tuple)))
        self.max_heights = []
        self.max_widths = []
        self.offset = offset

    def _get_controls(self):
        controls = []
        for row in self.content:
            for cell in row:
                controls += cell._get_controls()
        return controls

    def size(self, dialog):
        self.max_heights = [0] * len(self.content)
        width = 0
        for row in self.content:
            width = max(width, len(row))
        self.max_widths = [self.padding] * width
        row_index = 0
        for row in self.content:
            max_height = self.padding
            col_index = 0
            for cell in row:
                if cell is not None:
                    cell.size(dialog)
                    width, height = cell.width, cell.height
                else:
                    width, height = 0
                max_height = max(max_height, height + self.padding)
                max_width = self.max_widths[col_index]
                max_width = max(max_width, width + self.padding)
                self.max_widths[col_index] = max_width
                col_index += 1
            self.max_heights[row_index] = max_height
            row_index += 1
        self.width = reduce(lambda x, y: x + y, self.max_widths) + self.padding
        self.height = reduce(lambda x, y: x + y, self.max_heights) \
            + self.padding

    def layout(self, x, y):
        Widget.layout(self, x, y)

        row_index = 0
        placement = Widget()
        placement.y = y + self.height - self.padding
        for row in self.content:
            col_index = 0
            placement.x = x
            placement.height = self.max_heights[row_index]
            placement.y -= placement.height
            for cell in row:
                placement.width = self.max_widths[col_index]
                cell.layout(*GetRelativePoint(placement, self.align,
                                              cell, self.align, self.offset))
                placement.x += placement.width
                col_index += 1
            row_index += 1

