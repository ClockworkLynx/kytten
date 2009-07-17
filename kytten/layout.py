# kytten/layout.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Layouts are arrangements of multiple Widgets.
#
# VerticalLayout: a stack of Widgets, one on top of another.
# HorizontalLayout: a row of Widgets, side by side.
# GridLayout: a table of Widgets.
# FreeLayout: an open area within which Widgets may be positioned freely,
#             relative to one of its anchor points.

import pyglet
from pyglet import gl

from widgets import Widget, Control, Spacer, Graphic, Label

# GUI layout constants

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
ANCHOR_BOTTOM_RIGHT = (VALIGN_BOTTOM, HALIGN_RIGHT)

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
    Arranges Widgets on top of each other, from top to bottom.
    """
    def __init__(self, content=[], align=HALIGN_CENTER, padding=5):
        """
        Creates a new VerticalLayout.

        @param content A list of Widgets to be arranged
        @param align HALIGN_LEFT if Widgets are to be left-justified,
                     HALIGN_CENTER if they should be centered, and
                     HALIGN_RIGHT if they are to be right-justified.
        @param padding This amount of padding is inserted between widgets.
        """
        assert isinstance(content, list) or isinstance(content, tuple)
        Widget.__init__(self)
        self.align = align
        self.padding = padding
        self.content = [x or Spacer() for x in content]
        self.expandable = []

    def _get_controls(self):
        """
        Returns Controls within the layout.
        """
        controls = []
        for item in self.content:
            controls += item._get_controls()
        return controls

    def add(self, item):
        """
        Adds a new Widget to the layout.

        @param item The Widget to be added
        """
        self.content.append(item or Spacer())
        self.saved_dialog.set_needs_layout()

    def delete(self):
        """Deletes all graphic elements within the layout."""
        for item in self.content:
            item.delete()
        Widget.delete(self)

    def expand(self, width, height):
        """
        Expands to fill available vertical space.  We split available space
        equally between all spacers.
        """
        available = int((height - self.height) / len(self.expandable))
        remainder = height - self.height - len(self.expandable) * available
        for item in self.expandable:
            if remainder > 0:
                item.expand(item.width, item.height + available + 1)
                remainder -= 1
            else:
                item.expand(item.width, item.height + available)
        self.height = height
        self.width = width

    def is_expandable(self):
        """True if we contain expandable content."""
        return len(self.expandable) > 0

    def remove(self, item):
        """
        Removes a Widget from the layout.

        @param item The Widget to be removed
        """
        item.delete()
        self.content.remove(item)
        self.saved_dialog.set_needs_layout()

    def layout(self, x, y):
        """
        Lays out the child Widgets, in order from top to bottom.

        @param x X coordinate of the lower left corner
        @param y Y coordinate of the lower left corner
        """
        Widget.layout(self, x, y)

        # Expand any expandable content to our width
        for item in self.content:
            if item.is_expandable() and item.width < self.width:
                item.expand(self.width, item.height)

        top = y + self.height
        if self.align == HALIGN_RIGHT:
            for item in self.content:
                item.layout(x + self.width - item.width,
                            top - item.height)
                top -= item.height + self.padding
        elif self.align == HALIGN_CENTER:
            for item in self.content:
                item.layout(x + self.width/2 - item.width/2,
                            top - item.height)
                top -= item.height + self.padding
        else: # HALIGN_LEFT
            for item in self.content:
                item.layout(x, top - item.height)
                top -= item.height + self.padding

    def set(self, content):
        """
        Sets an entirely new set of Widgets, discarding the old.

        @param content The new list of Widgets
        """
        self.delete()
        self.content = content
        self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        """
        Calculates size of the layout, based on its children.

        @param dialog The Dialog which contains the layout
        """
        if dialog is None:
            return
        Widget.size(self, dialog)
        if len(self.content) < 2:
            height = 0
        else:
            height = -self.padding
        width = 0
        for item in self.content:
            item.size(dialog)
            height += item.height + self.padding
            width = max(width, item.width)
        self.width, self.height = width, height
        self.expandable = [x for x in self.content if x.is_expandable()]

    def teardown(self):
        for item in self.content:
            item.teardown()
        self.content = []
        Widget.teardown(self)

class HorizontalLayout(VerticalLayout):
    """
    Arranges Widgets from left to right.
    """
    def __init__(self, content=[], align=VALIGN_CENTER, padding=5):
        """
        Creates a new HorizontalLayout.

        @param content A list of Widgets to be arranged
        @param align VALIGN_TOP if Widgets are to be aligned to the top
                     VALIGN_CENTER if they should be centered, and
                     VALIGN_BOTTOM if they should be aligned to the bottom.
        @param padding This amount of padding is inserted around the edge
                       of the widgets and between widgets.
        """
        VerticalLayout.__init__(self, content, align, padding)

    def expand(self, width, height):
        """
        Expands to fill available horizontal space.  We split available space
        equally between all spacers.
        """
        available = int((width - self.width) / len(self.expandable))
        remainder = height - self.height - len(self.expandable) * available
        for item in self.expandable:
            if remainder > 0:
                item.expand(item.width + available + 1, item.height)
                remainder -= 1
            else:
                item.expand(item.width + available, item.height)
        self.width = width

    def layout(self, x, y):
        """
        Lays out the child Widgets, in order from left to right.

        @param x X coordinate of the lower left corner
        @param y Y coordinate of the lower left corner
        """
        Widget.layout(self, x, y)

        # Expand any expandable content to our height
        for item in self.content:
            if item.is_expandable() and item.height < self.height:
                item.expand(item.width, self.height)

        left = x
        if self.align == VALIGN_TOP:
            for item in self.content:
                item.layout(left, y + self.height - item.height)
                left += item.width + self.padding
        elif self.align == VALIGN_CENTER:
            for item in self.content:
                item.layout(left, y + self.height/2 - item.height/2)
                left += item.width + self.padding
        else: # VALIGN_BOTTOM
            for item in self.content:
                item.layout(left, y)
                left += item.width + self.padding

    def size(self, dialog):
        """
        Calculates size of the layout, based on its children.

        @param dialog The Dialog which contains the layout
        """
        if dialog is None:
            return
        Widget.size(self, dialog)
        height = 0
        if len(self.content) < 2:
            width = 0
        else:
            width = -self.padding
        for item in self.content:
            item.size(dialog)
            height = max(height, item.height)
            width += item.width + self.padding
        self.width, self.height = width, height
        self.expandable = [x for x in self.content if x.is_expandable()]

class GridLayout(Widget):
    """
    Arranges Widgets in a table.  Each cell's height and width are set to
    the maximum width of any Widget in its column, or the maximum height of
    any Widget in its row.

    Widgets are by default aligned to the top left corner of their cells.
    Another anchor point may be specified, i.e. ANCHOR_CENTER will ensure
    that Widgets are centered within cells.
    """
    def __init__(self, content=[[]], anchor=ANCHOR_TOP_LEFT, padding=5,
                 offset=(0, 0)):
        """
        Defines a new GridLayout.

        @param content A list of rows, each of which is a list of cells
                       within that row.  'None' may be used for empty cells,
                       and rows do not need to all be the same length.
        @param anchor Alignment of
        """
        assert ((isinstance(content, list) or isinstance(content, tuple)) and
                (len(content) == 0 or (isinstance(content[0], list) or
                                       isinstance(content[0], tuple))))
        Widget.__init__(self)
        self.content = content
        self.anchor = anchor
        self.padding = padding
        self.offset = offset
        self.max_heights = []
        self.max_widths = []

    def _get_controls(self):
        """
        Returns Controls within the layout.
        """
        controls = []
        for row in self.content:
            for cell in row:
                if cell is not None:
                    controls += cell._get_controls()
        return controls

    def add_row(self, row):
        """
        Adds a new row to the layout

        @param row An array of widgets, or None for cells without widgets
        """
        assert isinstance(row, tuple) or isinstance(row, list)
        self.content.append(row)
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def delete(self):
        """Deletes all graphic elements within the layout."""
        for row in self.content:
            for cell in row:
                cell.delete()
        Widget.delete(self)

    def delete_row(self, row):
        """
        Deletes a row from the layout

        @param row Index of row
        """
        if len(self.content) <= row:
            return
        row = self.content.pop(row)
        for column in row:
            if column is not None:
                column.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def get(self, column, row):
        """
        Returns the widget located at a given column and row, or None.

        @param column Column of cell
        @param row Row of cell
        """
        if row >= len(self.content):
            return None
        row = self.content[row]
        if column >= len(row):
            return None
        else:
            return row[column]

    def layout(self, x, y):
        """
        Lays out all Widgets within this layout.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        Widget.layout(self, x, y)

        row_index = 0
        placement = Widget()
        placement.y = y + self.height
        for row in self.content:
            col_index = 0
            placement.x = x
            placement.height = self.max_heights[row_index]
            placement.y -= placement.height
            for cell in row:
                placement.width = self.max_widths[col_index]
                if cell is not None:
                    if cell.is_expandable():
                        cell.expand(placement.width, placement.height)
                    cell.layout(*GetRelativePoint(placement, self.anchor,
                                                  cell, self.anchor,
                                                  self.offset))
                placement.x += placement.width
                col_index += 1
            row_index += 1

    def set(self, column, row, item):
        """
        Sets the content of a cell within the grid.

        @param column The column of the cell to be set
        @param row The row of the cell to be set
        @param item The new Widget to be set in that cell
        """
        if len(self.content) <= row:
            self.content = list(self.content) + \
                           [] * (row - len(self.content) + 1)
        if len(self.content[row]) <= column:
            self.content[row] = list(self.content[row]) + \
                [None] * (column - len(self.content[row]) + 1)
        if self.content[row][column] is not None:
            self.content[row][column].delete()
        self.content[row][column] = item
        self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        """Recalculates our size and the maximum widths and heights of
        each row and column in our table.

        @param dialog The Dialog within which we are contained
        """
        if dialog is None:
            return
        Widget.size(self, dialog)
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
                    width = height = 0
                max_height = max(max_height, height + self.padding)
                max_width = self.max_widths[col_index]
                max_width = max(max_width, width + self.padding)
                self.max_widths[col_index] = max_width
                col_index += 1
            self.max_heights[row_index] = max_height
            row_index += 1
        if self.max_widths:
            self.width = reduce(lambda x, y: x + y, self.max_widths) \
                - self.padding
        else:
            self.width = 0
        if self.max_heights:
            self.height = reduce(lambda x, y: x + y, self.max_heights) \
                - self.padding
        else:
            self.height = 0

    def teardown(self):
        for row in self.content:
            for cell in row:
                cell.teardown()
        self.content = []
        Widget.teardown(self)

class FreeLayout(Spacer):
    """
    FreeLayout defines a rectangle on the screen where Widgets may be placed
    freely, in relation to one of its anchor points.  There is no constraints
    against the Widgets overlapping.

    FreeLayout will expand to fill available space in layouts; thus you could
    place a FreeLayout as one half of a VerticalLayout, lay out controls in
    the other half, and be assured the FreeLayout would be resized to the
    width of the overall Dialog.
    """
    def __init__(self, width=0, height=0, content=[]):
        """
        Creates a new FreeLayout.

        @param width Minimum width of FreeLayout area
        @param height Minimum height of FreeLayout area
        @param content A list of placement/Widget tuples, in the form:
                       [(ANCHOR_TOP_LEFT, 0, 0, YourWidget()),
                        (ANCHOR_TOP_RIGHT, 0, 0, YourWidget()),
                        (ANCHOR_CENTER, 30, -20, YourWidget())]
            where each tuple is (anchor, offset-x, offset-y, widget)
        """
        Spacer.__init__(self, width, height)
        self.content = content

    def _get_controls(self):
        """Returns controls within the FreeLayout"""
        controls = []
        for anchor, x, y, item in self.content:
            controls += item._get_controls()
        return controls

    def add(self, anchor, x, y, widget):
        """
        Adds a new Widget to the FreeLayout.

        @param dialog Dialog which contains the FreeLayout
        @param anchor Anchor point to set for the widget
        @param x X-coordinate of offset from anchor point; positive is to
                 the right
        @param y Y-coordinate of offset from anchor point; positive is upward
        @param widget The Widget to be added
        """
        self.content.append( (anchor, x, y, widget) )
        self.saved_dialog.set_needs_layout()

    def layout(self, x, y):
        """
        Lays out Widgets within the FreeLayout.  We make no attempt to
        assure there's enough space for them.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        Spacer.layout(self, x, y)
        for anchor, offset_x, offset_y, widget in self.content:
            x, y = GetRelativePoint(self, anchor, widget, anchor,
                                    (offset_x, offset_y))
            widget.layout(x, y)

    def remove(self, dialog, widget):
        """
        Removes a widget from the FreeLayout.

        @param dialog Dialog which contains the FreeLayout
        @param widget The Widget to be removed
        """
        self.content = [x for x in self.content if x[3] != widget]

    def size(self, dialog):
        """
        Calculate size of the FreeLayout and all Widgets inside

        @param dialog The Dialog which contains the FreeLayout
        """
        if dialog is None:
            return
        Spacer.size(self, dialog)
        for anchor, offset_x, offset_y, widget in self.content:
            widget.size(dialog)

    def teardown(self):
        for _, _, _, item in self.content:
            item.teardown()
        self.content = []
        Widget.teardown(self)

