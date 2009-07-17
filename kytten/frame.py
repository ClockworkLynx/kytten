# kytten/frame.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Classes which wrap one Widget.

# Wrapper: a base class for Widgets which contain one other Widget.
# Frame: positions its contained Widget within a graphic, which it stretches
#        to cover the Widget's area, or the space within which it is contained.
# TitleFrame: like Frame, but has a title region on top as well.

from widgets import Widget, Control, Graphic, Label
from layout import HorizontalLayout, VerticalLayout, GetRelativePoint
from layout import VALIGN_BOTTOM, HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT
from layout import ANCHOR_CENTER

class Wrapper(Widget):
    """
    Wrapper is simply a wrapper around a widget.  While the default
    Wrapper does nothing more interesting, subclasses might decorate the
    widget in some fashion, i.e. Panel might place the widget onto a
    panel, or Scrollable might provide scrollbars to let the widget
    be panned about within its display area.
    """
    def __init__(self, content=None,
                 is_expandable=False, anchor=ANCHOR_CENTER, offset=(0, 0)):
        """
        Creates a new Wrapper around an included Widget.

        @param content The Widget to be wrapped.
        """
        Widget.__init__(self)
        self.content = content
        self.expandable = is_expandable
        self.anchor = anchor
        self.content_offset = offset

    def _get_controls(self):
        """Returns Controls contained by the Wrapper."""
        return self.content._get_controls()

    def delete(self):
        """Deletes graphic elements within the Wrapper."""
        if self.content is not None:
            self.content.delete()
        Widget.delete(self)

    def expand(self, width, height):
        if self.content.is_expandable():
            self.content.expand(width, height)
        self.width = width
        self.height = height

    def is_expandable(self):
        return self.expandable

    def layout(self, x, y):
        """
        Assigns a new position to the Wrapper.

        @param x X coordinate of the Wrapper's lower left corner
        @param y Y coordinate of the Wrapper's lower left corner
        """
        Widget.layout(self, x, y)
        if self.content is not None:
            x, y = GetRelativePoint(
                self, self.anchor,
                self.content, self.anchor, self.content_offset)
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
        if dialog is None:
            return
        Widget.size(self, dialog)
        if self.content is not None:
            self.content.size(dialog)
            self.width, self.height = self.content.width, self.content.height
        else:
            self.width = self.height = 0

    def teardown(self):
        self.content.teardown()
        self.content = None
        Widget.teardown(self)

class Frame(Wrapper):
    """
    Frame draws an untitled frame which encloses the dialog's content.
    """
    def __init__(self, content=None, path=['frame'], image_name='image',
                 is_expandable=False, anchor=ANCHOR_CENTER,
                 use_bg_group=False):
        """
        Creates a new Frame surrounding a widget or layout.
        """
        Wrapper.__init__(self, content,
                         is_expandable=is_expandable, anchor=anchor)
        self.frame = None
        self.path = path
        self.image_name = image_name
        self.use_bg_group = use_bg_group

    def delete(self):
        """
        Removes the Frame's graphical elements.
        """
        if self.frame is not None:
            self.frame.delete()
            self.frame = None
        Wrapper.delete(self)

    def expand(self, width, height):
        if self.content.is_expandable():
            content_width, content_height = \
                         self.frame.get_content_size(width, height)
            self.content.expand(content_width, content_height)
        self.width, self.height = width, height

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
        interior = Widget(width, height)
        interior.x, interior.y = x, y
        x, y = GetRelativePoint(interior, self.anchor,
                                self.content, self.anchor, self.content_offset)
        self.content.layout(x, y)

    def size(self, dialog):
        """
        Determine minimum size of the Frame.

        @param dialog Dialog which contains the Frame
        """
        if dialog is None:
            return
        Wrapper.size(self, dialog)
        if self.frame is None:
            if self.use_bg_group:
                group = dialog.bg_group
            else:
                group = dialog.panel_group
            template = dialog.theme[self.path][self.image_name]
            self.frame = template.generate(
                dialog.theme[self.path]['gui_color'],
                dialog.batch,
                group)
        self.width, self.height = self.frame.get_needed_size(
            self.content.width, self.content.height)

class TitleFrame(VerticalLayout):
    def __init__(self, title, content):
        VerticalLayout.__init__(self, content=[
                HorizontalLayout([
                    Graphic(path=["titlebar", "left"], is_expandable=True),
                    Frame(Label(title, path=["titlebar"]),
                          path=["titlebar", "center"]),
                    Graphic(path=["titlebar", "right"], is_expandable=True),
                ], align=VALIGN_BOTTOM, padding=0),
                Frame(content, path=["titlebar", "frame"], is_expandable=True),
            ], padding=0)

class SectionHeader(HorizontalLayout):
    def __init__(self, title, align=HALIGN_CENTER):
        if align == HALIGN_LEFT:
            left_expand = False
            right_expand = True
        elif align == HALIGN_CENTER:
            left_expand = True
            right_expand = True
        else:  # HALIGN_RIGHT
            left_expand = True
            right_expand = False

        HorizontalLayout.__init__(self, content=[
                Graphic(path=["section", "left"], is_expandable=left_expand),
                Frame(Label(title, path=["section"]),
                      path=['section', 'center'],
                      use_bg_group=True),
                Graphic(path=["section", "right"], is_expandable=right_expand),
            ], align=VALIGN_BOTTOM, padding=0)

class FoldingSection(Control, VerticalLayout):
    def __init__(self, title, content=None, is_open=True, align=HALIGN_CENTER):
        Control.__init__(self)
        if align == HALIGN_LEFT:
            left_expand = False
            right_expand = True
        elif align == HALIGN_CENTER:
            left_expand = True
            right_expand = True
        else:  # HALIGN_RIGHT
            left_expand = True
            right_expand = False

        self.is_open = is_open
        self.folding_content = content
        self.book = Graphic(self._get_image_path())

        self.header = HorizontalLayout([
            Graphic(path=["section", "left"], is_expandable=left_expand),
            Frame(HorizontalLayout([
                      self.book,
                      Label(title, path=["section"]),
                  ]), path=["section", "center"],
                  use_bg_group=True),
            Graphic(path=["section", "right"], is_expandable=right_expand),
            ], align=VALIGN_BOTTOM, padding=0)
        layout = [self.header]
        if self.is_open:
            layout.append(content)

        VerticalLayout.__init__(self, content=layout, align=align)

    def _get_controls(self):
        return VerticalLayout._get_controls(self) + \
               [(self, self.header.x, self.header.x + self.header.width,
                       self.header.y + self.header.height, self.header.y)]

    def _get_image_path(self):
        if self.is_open:
            return ["section", "opened"]
        else:
            return ["section", "closed"]

    def hit_test(self, x, y):
        return self.header.hit_test(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.is_open = not self.is_open
        self.book.delete()
        self.book.path = self._get_image_path()
        if self.is_open:
            self.add(self.folding_content)
        else:
            self.remove(self.folding_content)
            self.folding_content.delete()

    def teardown(self):
        self.folding_content.teardown()
        self.folding_content = None
        VerticalLayout.teardown(self)