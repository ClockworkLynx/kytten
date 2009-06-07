# kytten/layout.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

from widgets import Widget, Control, Text

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
        self.width, self.height = self.min_width, self.min_height

class Wrapper(Widget):
    """
    Wrapper is simply a wrapper around a widget.  While the default
    Wrapper does nothing more interesting, subclasses might decorate the
    widget in some fashion, i.e. Panel might place the widget onto a
    panel, or ScrollablePane might provide scrollbars to let the widget
    be panned about within its display area.
    """
    def __init__(self, content=None):
        """
        Creates a new Wrapper around an included Widget.

        @param content The Widget to be wrapped.
        """
        Widget.__init__(self)
        self.content = content

    def _get_controls(self):
        """Returns Controls contained by the Wrapper."""
        return self.content._get_controls()

    def delete(self):
        """Deletes graphic elements within the Wrapper."""
        if self.content is not None:
            self.content.delete()
        Widget.delete(self)

    def layout(self, x, y):
        """
        Assigns a new position to the Wrapper.

        @param x X coordinate of the Wrapper's lower left corner
        @param y Y coordinate of the Wrapper's lower left corner
        """
        Widget.layout(self, x, y)
        if self.content is not None:
            self.content.layout(x, y)

    def set(self, dialog, content):
        """
        Sets a new Widget to be contained in the Wrapper.

        @param dialog The Dialog which contains the Wrapper
        @param content The new Widget to be wrapped
        """
        if self.content is not None:
            self.content.delete()
        self.content = content
        dialog.set_needs_layout()

    def size(self, dialog):
        """
        The default Wrapper wraps up its Widget snugly.

        @param dialog The Dialog which contains the Wrapper
        """
        if self.content is not None:
            self.content.size(dialog)
            self.width, self.height = self.content.width, self.content.height
        else:
            self.width = self.height = 0

class Frame(Wrapper):
    """
    Frame draws an untitled frame which encloses the dialog's content.
    """
    def __init__(self, content=None):
        """
        Creates a new Frame surrounding a widget or layout.
        """
        Wrapper.__init__(self, content)
        self.frame = None

    def delete(self):
        """
        Removes the Frame's graphical elements.
        """
        if self.frame is not None:
            self.frame.delete()
            self.frame = None
        Wrapper.delete(self)

    def layout(self, x, y):
        """
        Positions the Frame.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        self.x, self.y = x, y
        self.frame.update(x, y, self.width, self.height)

        # In some cases the frame graphic element may allocate more space for
        # the content than the content actually fills, due to repeating
        # texture constraints.  Always center the content.
        x, y, width, height = self.frame.get_content_region()
        self.content.layout(x + width/2 - self.content.width/2,
                            y + height/2 - self.content.height/2)

    def size(self, dialog):
        """
        Determine minimum size of the Frame.

        @param dialog Dialog which contains the Frame
        """
        Wrapper.size(self, dialog)
        if self.frame is None:
            frame_template = dialog.theme['frame']['image']
            self.frame = frame_template.generate(dialog.theme['gui_color'],
                                                 dialog.batch,
                                                 dialog.panel_group)
        self.width, self.height = self.frame.get_needed_size(
            self.content.width, self.content.height)

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

    def add(self, dialog, item):
        """
        Adds a new Widget to the layout.

        @param dialog The Dialog which contains the layout
        @param item The Widget to be added
        """
        self.content.append(item or Spacer())
        if self.dialog is not None:
            self.dialog.set_needs_layout()

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
        for item in self.expandable:
            item.expand(item.width, item.height + available)
        self.height = height

    def is_expandable(self):
        """True if we contain expandable content."""
        return len(self.expandable) > 0

    def remove(self, dialog, item):
        """
        Removes a Widget from the layout.

        @param dialog The Dialog which contains the layout
        @param item The Widget to be removed
        """
        self.content.remove(item)
        if self.dialog is not None:
            self.dialog.needs_layout = True

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

    def set(self, dialog, content):
        """
        Sets an entirely new set of Widgets, discarding the old.

        @param dialog The Dialog which contains the layout
        @param content The new list of Widgets
        """
        self.delete()
        self.content = content
        self.dialog.set_needs_layout()

    def size(self, dialog):
        """
        Calculates size of the layout, based on its children.

        @param dialog The Dialog which contains the layout
        """
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
        for item in self.expandable:
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
                (isinstance(content[0], list) or
                 isinstance(content[0], tuple)))
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

    def delete(self):
        """Deletes all graphic elements within the layout."""
        for row in self.content:
            for cell in row:
                cell.delete()
        Widget.delete(self)

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

    def set(self, dialog, column, row, item):
        """
        Sets the content of a cell within the grid.

        @param dialog The Dialog which contains the layout
        @param column The column of the cell to be set
        @param row The row of the cell to be set
        @param item The new Widget to be set in that cell
        """
        if len(self.content) < row:
            self.content = list(self.content) + [] * (row - len(self.content))
        if len(self.content[row]) < column:
            self.content[row] = list(self.content[row]) + \
                [None] * (column - len(self.content[row]))
        if self.content[row][column] is not None:
            self.content[row][column].delete()
        self.content[row][column] = item
        dialog.set_needs_layout()

    def size(self, dialog):
        """Recalculates our size and the maximum widths and heights of
        each row and column in our table.

        @param dialog The Dialog within which we are contained
        """
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
        self.width = reduce(lambda x, y: x + y, self.max_widths) \
                   - self.padding
        self.height = reduce(lambda x, y: x + y, self.max_heights) \
                    - self.padding

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

    def add(self, dialog, anchor, x, y, widget):
        """
        Adds a new Widget to the FreeLayout.

        @param dialog Dialog which contains the FreeLayout
        @param anchor Anchor point to set for the widget
        @param x X-coordinate of offset from anchor point; positive is to
                 the right
        @param y Y-coordinate of offset from anchor point; positive is upward
        @param widget The Widget to be added
        """
        self.content.append( (dialog, anchor, x, y, widget) )
        dialog.set_needs_layout()

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
        Spacer.size(self, dialog)
        for anchor, offset_x, offset_y, widget in self.content:
            widget.size(dialog)

class HScrollbar(Control):
    """
    A horizontal scrollbar.  Position is measured from 0.0 to 1.0, and bar
    size is set as a percentage of the maximum.
    """
    def __init__(self, width, left, space, bar, right, left_max, right_max):
        """
        Creates a new scrollbar.  At the outset, we are presented with maximum
        width and the templates to use.

        @param width Width of the area for which we are a scrollbar
        @param left Template to generate left graphic element
        @param space Template to generate space graphic element
        @param bar Template to generate bar graphic element
        @param right Template to generate right graphic element
        @param left_max Template to generate left max graphic element
        @param right_max Template to generate right max graphic element
        """
        Control.__init__(self, width=width, height=left.height)
        self.__init2__(width, left, space, bar, right, left_max, right_max)

    def __init2__(self, width, left, space, bar, right, left_max, right_max):
        """
        HScrollbar and VScrollbar share similiar data structures, which this
        function initializes.

        @param width Width of the area for which we are a scrollbar
        @param left Template to generate left graphic element
        @param space Template to generate space graphic element
        @param bar Template to generate bar graphic element
        @param right Template to generate right graphic element
        @param left_max Template to generate left max graphic element
        @param right_max Template to generate right max graphic element
        """
        self.left_template = left
        self.space_template = space
        self.bar_template = bar
        self.right_template = right
        self.left_max_template = left_max
        self.right_max_template = right_max
        self.left = None
        self.space = None
        self.right = None
        self.bar = None
        self.pos = 0.0
        self.bar_width = 0.5
        self.is_dragging = False

    def _get_left_region(self):
        """
        Return area of the left button (x, y, width, height)
        """
        return self.x, self.y, self.left_template.width, self.height

    def _get_right_region(self):
        """
        Return area of the right button (x, y, width, height)
        """
        return (self.x + self.width - self.right_template.width, self.y,
                self.right_template.width, self.height)

    def _get_space_region(self):
        """
        Return area of the space in which the bar moves
        (x, y, width, height)
        """
        return (self.x + self.left_template.width, self.y,
                self.width - self.left_template.width -
                    self.right_template.width,
                self.height)

    def _get_bar_region(self):
        """
        Return area of the bar within the scrollbar (x, y, width, height)
        """
        self.pos = max(min(self.pos, 1.0 - self.bar_width), 0.0)
        space_width = self.width - self.left_template.width \
                    - self.right_template.width
        return (int(self.x + self.left_template.width +
                    self.pos * space_width),
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
        self.left.update(*self._get_left_region())
        self.right.update(*self._get_right_region())
        self.space.update(*self._get_space_region())
        self.bar.update(*self._get_bar_region())

    def on_mouse_drag(self, dialog, x, y, dx, dy, buttons, modifiers):
        """
        We drag the bar only if the user had previously clicked on the bar

        @param dialog Dialog which contains the scrollbar
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
            dialog.set_needs_layout()
            return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        """
        If the mouse press falls within the space, move the bar over to the
        mouse.  Otherwise, activate scrolling.

        @param dialog Dialog which contains the scrollbar
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
            dialog.set_needs_layout()

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        """
        Cancels dragging or scrolling

        @param dialog Dialog which contains the scrollbar
        @param x X coordinate of mouse
        @param y Y coordinate of mouse
        @param button Button being released
        @param modifiers Modifiers to apply to button
        """
        self.is_dragging = False

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
        self.bar.update(*self._get_bar_region())

    def size(self, dialog):
        """
        Creates scrollbar components.
        """
        if self.left is None:
            if self.pos > 0.0:
                self.left = self.left_template.generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.fg_group)
            else:
                self.left = self.left_max_template.generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.fg_group)
            self.height = self.left.height
        if self.space is None:
            self.space = self.space_template.generate(
                dialog.theme['gui_color'], dialog.batch, dialog.fg_group)
        if self.bar is None:
            self.bar = self.bar_template.generate(
                dialog.theme['gui_color'], dialog.batch, dialog.fg_group)
        if self.right is None:
            if self.pos <= 1.0 - self.bar_width:
                self.right = self.right_template.generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.fg_group)
            else:
                self.right = self.right_max_template.generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.fg_group)

class VScrollbar(HScrollbar):
    """
    A vertical scrollbar.  Position is measured from 0.0 to 1.0, and bar size
    is set as a percentage of the maximum.  Note that left is top, and
    right is bottom, from the viewpoint of the VScrollbar.
    """
    def __init__(self, height, up, space, bar, down, up_max, down_max):
        """
        Creates a new scrollbar.  At the outset, we are presented with maximum
        height and the templates to use.

        @param height Height of the area for which we are a scrollbar
        @param up Template to generate up graphic element
        @param space Template to generate space graphic element
        @param bar Template to generate bar graphic element
        @param down Template to generate down graphic element
        @param up_max Template to generate up max graphic element
        @param down_max Template to generate down max graphic element
        """
        Control.__init__(self, width=up.width, height=height)
        self.__init2__(height, up, space, bar, down, up_max, down_max)

    def _get_left_region(self):
        """Returns the area occupied by the up button
        (x, y, width, height)"""
        return (self.x, self.y + self.height - self.left_template.height,
                self.width, self.left.height)

    def _get_right_region(self):
        """Returns the area occupied by the down button
        (x, y, width, height)"""
        return (self.x, self.y, self.width, self.right_template.height)

    def _get_space_region(self):
        """Returns the area occupied by the space between up and down
        buttons (x, y, width, height)"""
        return (self.x,
                self.y + self.right_template.height,
                self.width,
                self.height - self.left_template.width -
                    self.right_template.width)

    def _get_bar_region(self):
        """Returns the area occupied by the bar (x, y, width, height)"""
        self.pos = max(min(self.pos, 1.0 - self.bar_width), 0.0)
        space_height = self.height - self.left_template.height \
                     - self.right_template.height
        top = self.y + self.height - self.left_template.height
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
        self.bar.update(*self._get_bar_region())

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

class Scrollable(Wrapper, Control):
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
        Control.__init__(self)
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
        self.controls = None
        self.hover = None
        self.focus = None
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

    def hit_test(self, x, y):
        """
        We only intercept events for the content region, not for
        our scrollbars.  They can handle themselves!
        """
        return x >= self.content_x and y >= self.content_y and \
               x < self.content_x + self.content_width and \
               y < self.content_y + self.content_height

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
        self.root_group.x, self.root_group.y = x, y
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

    def on_key_press(self, dialog, symbol, modifiers):
        """
        Pass keypresses to our focus.

        TODO(lynx): we can't currently step between focusable components
        within a scrollable region.  Will need to think about this a bit.
        """
        if self.focus is not None:
            self.focus.dispatch_event('on_key_press',
                                      self, symbol, modifiers)
            return pyglet.event.EVENT_HANDLED

    def on_lose_focus(self, dialog):
        """
        If we're no longer focused by the Dialog, remove our own focus
        """
        self.set_focus(None)

    def on_lose_highlight(self, dialog):
        """
        If we're no longer highlighted by the Dialog, remove our own
        highlight
        """
        self.set_hover(None)

    def on_mouse_drag(self, dialog, x, y, dx, dy, buttons, modifiers):
        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_drag', self,
                                      x, y, dx, dy, buttons, modifiers)
            return pyglet.event.EVENT_HANDLED

    def on_mouse_motion(self, dialog, x, y, dx, dy):
        if self.hover is not None and self.hover.hit_test(x, y):
            self.hover.dispatch_event('on_mouse_motion', self, x, y, dx, dy)
        new_hover = None
        for control in self.controls:
            if control.hit_test(x, y):
                new_hover = control
                break
        self.set_hover(new_hover)
        if self.hover is not None:
            self.hover.dispatch_event('on_mouse_motion', self, x, y, dx, dy)

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        if self.focus is not None and self.focus.hit_test(x, y):
            self.focus.dispatch_event('on_mouse_press', self,
                                      x, y, button, modifiers)
            return pyglet.event.EVENT_HANDLED
        else:
            if self.hit_test(x, y):
                self.set_focus(self.hover)
                if self.focus is not None:
                    self.focus.dispatch_event('on_mouse_press', self,
                                              x, y, button, modifiers)
                return pyglet.event.EVENT_HANDLED
            else:
                self.set_focus(None)

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        retval = pyglet.event.EVENT_UNHANDLED
        self.is_dragging = False
        if self.focus is not None:
            self.focus.dispatch_event('on_mouse_release', self,
                                             x, y, button, modifiers)
            retval = pyglet.event.EVENT_HANDLED
        self.on_mouse_motion(dialog, x, y, 0, 0)
        return retval

    def on_text(self, dialog, text):
        if self.focus and text != u'\r':
            self.focus.dispatch_event('on_text', self, text)

    def on_text_motion(self, dialog, motion):
        if self.focus:
            self.focus.dispatch_event('on_text_motion', self, motion)

    def on_text_motion_select(self, dialog, motion):
        if self.focus:
            self.focus.dispatch_event('on_text_motion_select', self, motion)

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

    def set_needs_layout(self):
        self.needs_layout = True

    def size(self, dialog):
        """
        Recalculate the size of the Scrollable.

        @param dialog Dialog which contains us
        """
        if self.is_fixed_size:
            self.width, self.height = self.max_width, self.max_height

        if self.root_group is None: # do we need to re-clone Dialog?
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
                self.hscrollbar = HScrollbar(
                    self.max_width,
                    dialog.theme['hscrollbar']['image-left'],
                    dialog.theme['hscrollbar']['image-space'],
                    dialog.theme['hscrollbar']['image-bar'],
                    dialog.theme['hscrollbar']['image-right'],
                    dialog.theme['hscrollbar']['image-leftmax'],
                    dialog.theme['hscrollbar']['image-rightmax'])
            self.hscrollbar.size(dialog)
            self.hscrollbar.set(self.max_width, self.width)
        if self.always_show_scrollbars or \
           (self.max_height and self.height > self.max_height):
            if self.vscrollbar is None:
                self.vscrollbar = VScrollbar(
                    self.max_height,
                    dialog.theme['vscrollbar']['image-up'],
                    dialog.theme['vscrollbar']['image-space'],
                    dialog.theme['vscrollbar']['image-bar'],
                    dialog.theme['vscrollbar']['image-down'],
                    dialog.theme['vscrollbar']['image-upmax'],
                    dialog.theme['vscrollbar']['image-downmax'])
            self.vscrollbar.size(dialog)
            self.vscrollbar.set(self.max_height, self.height)

        self.width = min(self.max_width or self.width, self.width)
        self.content_width = self.width
        if self.vscrollbar is not None:
            self.width += self.vscrollbar.width
        self.height = min(self.max_height or self.height, self.height)
        self.content_height = self.height
        if self.hscrollbar is not None:
            self.height += self.hscrollbar.height

        self.controls = self.content._get_controls()

class MenuOption(Control):
    """
    MenuOption is a choice within a menu.  When selected, it inverts
    (inverted color against text-color background) to indicate that it
    has been chosen.
    """
    def __init__(self, text="", anchor=ANCHOR_CENTER, menu=None):
        Control.__init__(self)
        self.text = text
        self.anchor = anchor
        self.menu = menu
        self.label = None
        self.background = None
        self.highlight = None
        self.is_selected = False

    def expand(self, width, height):
        self.width = width
        self.height = height

    def is_expandable(self):
        return True

    def layout(self, x, y):
        self.x, self.y = x, y
        if self.background is not None:
            self.background.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)
        font = self.label.document.get_font()
        height = font.ascent - font.descent
        x, y = GetRelativePoint(self, self.anchor,
                                Widget(self.label.content_width, height),
                                self.anchor, (0, 0))
        self.label.x = x
        self.label.y = y - font.descent

    def on_gain_highlight(self, dialog):
        Control.on_gain_highlight(self, dialog)
        self.size(dialog) # to set up the highlight
        if self.highlight is not None:
            self.highlight.update(self.x, self.y,
                                  self.menu.width, self.height)

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        self.menu.select(dialog, self.text)

    def select(self, dialog):
        self.is_selected = True
        self.label.delete()
        self.label = None
        dialog.set_needs_layout()

    def size(self, dialog):
        if self.label is None:
            if self.is_selected:
                self.label = pyglet.text.Label(self.text,
                    color=dialog.theme['inverse_color'],
                    font_name=dialog.theme['font'],
                    font_size=dialog.theme['font_size'],
                    batch=dialog.batch,
                    group=dialog.fg_group)
            else:
                self.label = pyglet.text.Label(self.text,
                    color=dialog.theme['text_color'],
                    font_name=dialog.theme['font'],
                    font_size=dialog.theme['font_size'],
                    batch=dialog.batch,
                    group=dialog.fg_group)
            font = self.label.document.get_font()
            self.width = self.label.content_width
            self.height = font.ascent - font.descent

        if self.background is None:
            if self.is_selected:
                self.background = \
                    dialog.theme['menuoption']['image-highlight'].\
                        generate(dialog.theme['text_color'],
                                 dialog.batch,
                                 dialog.bg_group)
        if self.highlight is None:
            if self.is_highlight:
                self.highlight = \
                    dialog.theme['menuoption']['image-highlight'].\
                        generate(dialog.theme['highlight_color'],
                                 dialog.batch,
                                 dialog.highlight_group)

    def unselect(self, dialog):
        self.is_selected = False
        self.label.delete()
        self.label = None
        if self.background is not None:
            self.background.delete()
            self.background = None
        dialog.set_needs_layout()

class Menu(VerticalLayout):
    """
    Menu is a VerticalLayout of MenuOptions.  Moving the mouse across
    MenuOptions highlights them; clicking one selects it and causes Menu
    to send an on_click event.
    """
    def __init__(self, options=[], align=HALIGN_CENTER, padding=4,
                 on_select=None):
        menu_options = [MenuOption(option,
                                   anchor=(VALIGN_CENTER, align),
                                   menu=self) for option in options]
        self.options = dict(zip(options, menu_options))
        self.on_select = on_select
        self.selected = None
        VerticalLayout.__init__(self, menu_options,
                                align=align, padding=padding)

    def select(self, dialog, text):
        assert text in self.options
        if self.selected is not None:
            self.options[self.selected].unselect(dialog)
        self.selected = text
        menu_option = self.options[text]
        menu_option.select(dialog)

        if self.on_select is not None:
            self.on_select(text)