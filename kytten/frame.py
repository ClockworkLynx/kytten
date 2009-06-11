# kytten/frame.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

# Classes which wrap one Widget.

# Wrapper: a base class for Widgets which contain one other Widget.
# Frame: positions its contained Widget within a graphic, which it stretches
#        to cover the Widget's area, or the space within which it is contained.
# TitleFrame: like Frame, but has a title region on top as well.

from widgets import Widget, Graphic, Label
from layout import HorizontalLayout, VerticalLayout, VALIGN_BOTTOM

class Wrapper(Widget):
    """
    Wrapper is simply a wrapper around a widget.  While the default
    Wrapper does nothing more interesting, subclasses might decorate the
    widget in some fashion, i.e. Panel might place the widget onto a
    panel, or Scrollable might provide scrollbars to let the widget
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
    def __init__(self, content=None, component="frame", image_name="image"):
        """
        Creates a new Frame surrounding a widget or layout.
        """
        Wrapper.__init__(self, content)
        self.frame = None
        self.component = component
        self.image_name = image_name

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
            template = dialog.theme[self.component][self.image_name]
            self.frame = template.generate(dialog.theme['gui_color'],
                                           dialog.batch,
                                           dialog.panel_group)
        self.width, self.height = self.frame.get_needed_size(
            self.content.width, self.content.height)

class TitleFrame(VerticalLayout):
    def __init__(self, title, content):
        VerticalLayout.__init__(self, content=[
                HorizontalLayout([
                    Graphic("titlebar", "image-left", is_expandable=True),
                    Frame(Label(title, component="titlebar"),
                          component="titlebar", image_name="image-center"),
                    Graphic("titlebar", "image-right", is_expandable=True),
                ], align=VALIGN_BOTTOM, padding=0),
                Frame(content, "titlebar", "image-frame"),
            ], padding=0)

