# kytten/widgets.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from pyglet import gl

class Widget:
    """
    The base of all Kytten GUI elements.  Widgets correspond to areas on the
    screen and may (in the form of Controls) respond to user input.
    A simple Widget can be used as a fixed-area spacer.

    Widgets are constructed in two passes: first, they are created and
    passed into a Dialog, or added to a Dialog or one of its children,
    then the Dialog calls their size() method to get their size and their
    layout() method to place them on the screen.  When their size is gotten
    for the first time, they initialize any requisite graphic elements
    that could not be done at creation time.
    """
    def __init__(self, width=0, height=0):
        """
        Creates a new Widget.

        @param width Initial width
        @param height Initial height
        """
        self.x = self.y = 0
        self.width = width
        self.height = height

    def _get_controls(self):
        """
        Return this widget if it is a Control, or any children which
        are Controls.
        """
        return []

    def delete(self):
        """
        Deletes any graphic elements we have constructed.  Note that
        we may be asked to recreate them later.
        """
        pass

    def expand(self, width, height):
        """
        Expands the widget to fill the specified space given.

        @param width Available width
        @param height Available height
        """
        assert False, "Widget does not support expand"

    def hit_test(self, x, y):
        """
        True if the given point lies within our area.

        @param x X coordinate of point
        @param y Y coordinate of point
        @returns True if the point is within our area
        """
        return x >= self.x and x < self.x + self.width and \
               y >= self.y and y < self.y + self.height

    def is_expandable(self):
        """
        Returns true if the widget can expand to fill available space.
        """
        return False

    def layout(self, x, y):
        """
        Assigns a new location to this widget.

        @param x X coordinate of our lower left corner
        @param y Y coordinate of our lower left corner
        """
        self.x, self.y = x, y

    def size(self, dialog):
        """
        Constructs any graphic elements needed, and recalculates our size
        if necessary.

        @param dialog The Dialog which contains this Widget
        """
        pass

class Control(Widget, pyglet.event.EventDispatcher):
    """
    Controls are widgets which can accept events.

    Dialogs will search their children for a list of controls, and will
    then dispatch events to whichever control is currently the focus of
    the user's attention.
    """
    def __init__(self, id=None, value=None, width=0, height=0):
        """
        Creates a new Control.

        @param id Controls may have ids, which can be used to identify
                  them to the outside application.
        @param value Controls may be assigned values at start time.  The
                     values of all controls which have ids can be obtained
                     through the containing Dialog.
        @param x Initial X coordinate of lower left corner
        @param y Initial Y coordinate of lower left corner
        @param width Initial width
        @param height Initial height
        """
        Widget.__init__(self, width, height)
        self.id = id
        self.value = value
        pyglet.event.EventDispatcher.__init__(self)
        self.is_highlight = False
        self.is_focus = False

    def _get_controls(self):
        return [self]

    def get_cursor(self, x, y):
        return self.cursor

    def is_focus(self):
        return self.is_focus

    def is_highlight(self):
        return self.is_highlight

    def on_gain_focus(self, dialog):
        self.is_focus = True

    def on_gain_highlight(self, dialog):
        self.is_highlight = True

    def on_lose_focus(self, dialog):
        self.is_focus = False

    def on_lose_highlight(self, dialog):
        self.is_highlight = False

# Controls can potentially accept most of the events defined for the window,
# but in practice we'll only pass selected events from Dialog.  This avoids
# a large number of unsightly empty method declarations.
for event_type in pyglet.window.Window.event_types:
    Control.register_event_type(event_type)

Control.register_event_type('on_gain_focus')
Control.register_event_type('on_gain_highlight')
Control.register_event_type('on_lose_focus')
Control.register_event_type('on_lose_highlight')
Control.register_event_type('on_update')

class Block(Widget):
    """
    A simple widget which draws a crossed box.
    """
    def __init__(self, width, height):
        """
        Blocks occupy a fixed width and height.

        @param width Width
        @param height Height
        """
        Widget.__init__(self, width=width, height=height)
        self.vertex_list = None

    def _get_indices(self):
        """
        Defines a square with two crossed diagonals.

        @return An array of indices to update our indexed vertex list.
        """
        return (0, 1, 1, 2, 2, 3, 3, 0, 0, 2, 1, 3)

    def _get_vertices(self):
        """
        Defines the corners of the square.

        @return An array of coordinates for our indexed vertex list.
        """
        x1, y1 = self.x, self.y
        x2, y2 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
        """
        Deletes our vertex list.
        """
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def layout(self, x, y):
        """Places the vertex list at the new location.

        @param x X coordinate of our lower left corner
        @param y Y coordinate of our lower left corner
        """
        Widget.layout(self, x, y)
        self.vertex_list.vertices = self._get_vertices()

    def size(self, dialog):
        """Constructs a vertex list to draw a crossed square.

        @param dialog The Dialog within which we are contained
        """
        if self.vertex_list is None:
            self.vertex_list = dialog.batch.add_indexed(4, gl.GL_LINES,
                dialog.fg_group,
                self._get_indices(),
                ('v2i', self._get_vertices()),
                ('c4B', dialog.theme['gui_color'] * 4))

class Graphic(Widget):
    """
    Lays out a graphic from the theme, i.e. part of a title bar.
    """
    def __init__(self, component, image_name, is_expandable=False):
        Widget.__init__(self)
        self.component = component
        self.image_name = image_name
        self.expandable=is_expandable
        self.graphic = None

    def delete(self):
        if self.graphic is not None:
            self.graphic.delete()
            self.graphic = None

    def expand(self, width, height):
        if self.expandable:
            self.width, self.height = width, height
            self.graphic.update(self.x, self.y, self.width, self.height)

    def is_expandable(self):
        return self.expandable

    def layout(self, x, y):
        self.x, self.y = x, y
        self.graphic.update(x, y, self.width, self.height)

    def size(self, dialog):
        if self.graphic is None:
            template = dialog.theme[self.component][self.image_name]
            self.graphic = template.generate(dialog.theme['gui_color'],
                                             dialog.batch,
                                             dialog.fg_group)
        self.width, self.height = self.graphic.width, self.graphic.height

class Button(Control):
    """
    A simple text-labeled button.
    """
    def __init__(self, text="", id=None, on_click=None):
        """
        Creates a new Button.  The provided text will be used to caption the
        button.

        @param text Label for the button
        @param on_click Callback for the button
        """
        Control.__init__(self, id=id)
        self.text = text
        self.on_click = on_click
        self.label = None
        self.button = None
        self.highlight = None
        self.is_pressed = False

    def delete(self):
        """
        Clean up our graphic elements
        """
        Control.delete(self)
        if self.button is not None:
            self.button.delete()
            self.button = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def layout(self, x, y):
        """
        Places the Button.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        Control.layout(self, x, y)
        self.button.update(self.x, self.y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(self.x, self.y, self.width, self.height)
        x, y, width, height = self.button.get_content_region()
        font = self.label.document.get_font()
        self.label.x = x + width/2 - self.label.content_width/2
        self.label.y = y + height/2 - font.ascent/2 - font.descent

    def on_gain_highlight(self, dialog):
        Control.on_gain_highlight(self, dialog)
        self.size(dialog)
        self.highlight.update(self.x, self.y, self.width, self.height)

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        if not self.is_pressed:
            self.is_pressed = True

            # Delete the button to force it to be redrawn
            self.button.delete()
            self.button = None
            self.size(dialog)
            self.button.update(self.x, self.y, self.width, self.height)

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        if self.is_pressed:
            self.is_pressed = False

            # Delete the button to force it to be redrawn
            self.button.delete()
            self.button = None
            self.size(dialog)
            self.button.update(self.x, self.y, self.width, self.height)

            # Now, if mouse is still inside us, signal on_click
            if self.on_click is not None and self.hit_test(x, y):
                if self.id is not None:
                    self.on_click(id)
                else:
                    self.on_click()

    def size(self, dialog):
        """
        Sizes the Button.  If necessary, creates the graphic elements.

        @param dialog Dialog which contains the Button
        """
        if self.button is None:
            if self.is_pressed:
                self.button = dialog.theme['button']['image-down'].generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.bg_group)
            else:
                self.button = dialog.theme['button']['image'].generate(
                    dialog.theme['gui_color'], dialog.batch, dialog.bg_group)
        if self.highlight is None and self.is_highlight:
            self.highlight = dialog.theme['button']['image-highlight'].\
                generate(dialog.theme['highlight_color'],
                         dialog.batch,
                         dialog.bg_group)
        if self.label is None:
            self.label = pyglet.text.Label(self.text,
                font_name=dialog.theme['font'],
                font_size=dialog.theme['font_size'],
                color=dialog.theme['gui_color'],
                batch=dialog.batch, group=dialog.fg_group)

        # Treat the height of the label as ascent + descent
        font = self.label.document.get_font()
        height = font.ascent - font.descent # descent is negative
        self.width, self.height = self.button.get_needed_size(
            self.label.content_width, height)

class Label(Widget):
    """A wrapper around a simple text label."""
    def __init__(self, text="", bold=False):
        Widget.__init__(self)
        self.text = text
        self.bold = bold
        self.label = None

    def delete(self):
        if self.label is not None:
            self.label.delete()
            self.label = None

    def layout(self, x, y):
        Widget.layout(self, x, y)
        font = self.label.document.get_font()
        self.label.x = x
        self.label.y = y - font.descent

    def size(self, dialog):
        if self.label is None:
            self.label = pyglet.text.Label(
                self.text, bold=self.bold, color=dialog.theme['gui_color'],
                font_name=dialog.theme['font'],
                font_size=dialog.theme['font_size'],
                batch=dialog.batch, group=dialog.fg_group)
            font = self.label.document.get_font()
            self.width = self.label.content_width
            self.height = font.ascent - font.descent  # descent is negative

class Input(Control):
    """A text input field."""
    def __init__(self, id=None, text="", length=20, padding=0,
                 on_input=None):
        Control.__init__(self, id=id)
        self.text = text
        self.length = length
        self.padding = padding
        self.on_input = on_input
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.text_layout = None
        self.caret = None
        self.field = None
        self.highlight = None

    def delete(self):
        Control.delete(self)
        if self.text_layout is not None:
            self.text_layout.delete()
            self.text_layout = None
        if self.caret is not None:
            self.caret.delete()
            self.caret = None
        if self.field is not None:
            self.field.delete()
            self.field = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def get_text(self):
        return self.document.text

    def layout(self, x, y):
        self.x, self.y = x, y
        self.field.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

        # Adjust the text for font's descent
        x, y, width, height = self.field.get_content_region()
        self.text_layout.x = x + self.padding
        self.text_layout.y = y + self.padding

    def on_gain_highlight(self, dialog):
        Control.on_gain_highlight(self, dialog)
        self.set_highlight(dialog)

    def on_gain_focus(self, dialog):
        Control.on_gain_focus(self, dialog)
        self.set_highlight(dialog)
        if self.caret is not None:
            self.caret.visible = True
            self.caret.mark = 0
            self.caret.position = len(self.document.text)

    def on_lose_focus(self, dialog):
        Control.on_lose_focus(self, dialog)
        self.remove_highlight()
        if self.caret is not None:
            self.caret.visible = False
            self.caret.mark = self.caret.position = 0
        if self.on_input is not None:
            if self.id is not None:
                self.on_input(self.id, self.get_text())
            else:
                self.on_input(self.get_text())

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        self.remove_highlight()

    def on_mouse_drag(self, dialog, x, y, dx, dy, buttons, modifiers):
        return self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        return self.caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, dialog, text):
        self.caret.on_text(text)

    def on_text_motion(self, dialog, motion):
        return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, dialog, motion):
        return self.caret.on_text_motion_select(motion)

    def set_text(self, text):
        self.document.text = text
        self.caret.mark = self.caret.position = len(self.document.text)

    def remove_highlight(self):
        if not self.is_highlight and not self.is_focus:
            if self.highlight is not None:
                self.highlight.delete()
                self.highlight = None

    def set_highlight(self, dialog):
        if self.highlight is None:
            self.highlight = dialog.theme['input']['image-highlight'].\
                generate(color=dialog.theme['highlight_color'],
                         batch=dialog.batch,
                         group=dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def size(self, dialog):
        self.document.set_style(0, len(self.document.text),
                    dict(color=dialog.theme['text_color'],
                         font_name=dialog.theme['font'],
                         font_size=dialog.theme['font_size']))

        # Calculate the needed size based on the font size
        font = self.document.get_font(0)
        height = font.ascent - font.descent
        glyphs = font.get_glyphs('A_')
        width = max([x.width for x in glyphs])
        needed_width = self.length * width + 2 * self.padding
        needed_height = height + 2 * self.padding

        if self.text_layout is None:
            self.text_layout = pyglet.text.layout.IncrementalTextLayout(
                self.document, needed_width, needed_height,
                multiline=False,
                batch=dialog.batch, group=dialog.fg_group)
        if self.caret is None:
            self.caret = pyglet.text.caret.Caret(
                self.text_layout, color=dialog.theme['gui_color'][0:3])
            self.caret.visible = False
        if self.field is None:
            self.field = dialog.theme['input']['image'].generate(
                color=dialog.theme['gui_color'],
                batch=dialog.batch,
                group=dialog.bg_group)
        if self.highlight is None and self.is_highlight:
            self.set_highlight(dialog)

        self.width, self.height = self.field.get_needed_size(
            needed_width, needed_height)

class Document(Widget):
    """
    Allows you to embed a document within the GUI, which can then be scrolled
    using the Scrollable frame.

    Example:
    document = pyglet.text.decode_attributed(
	'''{align "center"}{bold True}Kytten{bold False}{align "left"}{}
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
''')

    # Set up a Dialog to scroll through the text
    dialog = kytten.Dialog(
	kytten.Frame(
	    kytten.Scrollable(
		kytten.Document(document, width=300),
		height=100,
	    ),
	),
	window=window, batch=batch, group=fg_group,
	anchor=kytten.ANCHOR_TOP_LEFT,
	theme=theme)
    window.push_handlers(dialog)
    """
    def __init__(self, document, width=1000, height=0):
        Widget.__init__(self, width, height)
        self.document = document
        self.content = None
        self.set_document_style = False

    def _do_set_document_style(self, attr, value):
        length = len(self.document.text)
        runs = [(start, end, doc_value) for start, end, doc_value in
                self.document.get_style_runs(attr).ranges(0, length)
                if doc_value is not None]
        if not runs:
            terminator = len(self.document.text)
        else:
            terminator = runs[0][0]
        self.document.set_style(0, terminator, {attr: value})

    def delete(self):
        if self.content is not None:
            self.content.delete()
            self.content = None

    def do_set_document_style(self, dialog):
        self.set_document_style = True

        # Check the style runs to make sure we don't stamp on anything
        # set by the user
        self._do_set_document_style('color', dialog.theme['text_color'])
        self._do_set_document_style('font_name', dialog.theme['font'])
        self._do_set_document_style('font_size', dialog.theme['font_size'])

    def expand(self, width, height):
        self.height = height
        self.width = width
        self.content.width = width
        self.content.height = self.content.content_height

    def is_expandable(self):
        return True

    def layout(self, x, y):
        self.content.begin_update()
        self.content.x = x
        self.content.y = y
        self.content.end_update()

    def size(self, dialog):
        if not self.set_document_style:
            self.do_set_document_style(dialog)
        if self.content is None:
            self.content = pyglet.text.layout.IncrementalTextLayout(
                self.document,
                self.width,
                0, # height is arbitrary
                multiline=True, batch=dialog.batch, group=dialog.fg_group)
        self.width = self.content.width
        self.height = self.content.height = self.content.content_height