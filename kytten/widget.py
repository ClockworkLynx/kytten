# kytten/widget.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

"""
Widgets.

These differ from graphic elements (presented in graphics.py) in that they
represent the control logic for GUI elements, not the display logic.  This
allows us to reskin widgets in different forms, i.e. we might want to have
an animated menu or objects that sparkle, which would require a more advanced
graphic element, but the control logic could remain the same.
"""

import pyglet
from pyglet import gl

import layout

class Widget:
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def _get_controls(self):
        return []

    def delete(self):
        pass

    def hit_test(self, x, y):
        return x >= self.x and y >= self.y and \
               x < self.x + self.width and \
               y < self.y + self.height

    def size(self, dialog):
        pass

    def layout(self, x, y):
        self.x, self.y = x, y

class Container(Widget):
    """
    The default container can contain a single element.
    """

    def __init__(self, content=None):
        Widget.__init__(self)
        self.content = content

    def _get_controls(self):
        return self.content._get_controls()

    def delete(self):
        if self.content is not None:
            self.content.delete()
        Widget.delete(self)

    def set(self, content):
        if self.content is not None:
            self.content.delete()
        self.content = content

    def size(self, dialog):
        if self.content is not None:
            self.content.size(dialog)
            self.width, self.height = self.content.width, self.content.height
        else:
            self.width = self.height = 0

    def layout(self, x, y):
        Widget.layout(self, x, y)
        if self.content is not None:
            self.content.layout(x, y)

class Control(Widget, pyglet.event.EventDispatcher):
    """
    Controls are widgets which can accept events.  They will add themselves
    to the Dialog's list of controls and can then handle focus and highlight
    events.
    """
    def __init__(self, x=0, y=0, width=0, height=0, cursor=None):
        Widget.__init__(self, x, y, width, height)
        pyglet.event.EventDispatcher.__init__(self)
        self.cursor = cursor
        self.is_highlight = False
        self.is_focus = False

    def _get_controls(self):
        return [self]

    def get_cursor(self, x, y):
        return self.cursor

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

class Block(Widget):
    """A simple widget which draws a crossed box occupying a certain amount
    of space."""
    def __init__(self, width, height):
        Widget.__init__(self, width=width, height=height)
        self.vertex_list = None

    def _get_indices(self):
        return (0, 1, 1, 2, 2, 3, 3, 0, 0, 2, 1, 3)

    def _get_vertices(self):
        x1, y1 = self.x, self.y
        x2, y2 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def remove(self):
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def size(self, dialog):
        if self.vertex_list is None:
            self.vertex_list = dialog.batch.add_indexed(4, gl.GL_LINES,
                dialog.fg_group,
                self._get_indices(),
                ('v2i', self._get_vertices()),
                ('c4B', dialog.stylesheet.color * 4))

    def layout(self, x, y):
        Widget.layout(self, x, y)
        self.vertex_list.vertices = self._get_vertices()

class Text(Widget):
    """A wrapper around a simple text label."""
    def __init__(self, text="", bold=False):
        Widget.__init__(self)
        self.text = text
        self.bold = bold
        self.label = None

    def remove(self):
        if self.label is not None:
            self.label.delete()
            self.label = None

    def layout(self, x, y):
        Widget.layout(self, x, y)
        self.label.update(x, y)

    def size(self, dialog):
        if self.label is None:
            self.label = dialog.get_provider().get_text(
                self.text, bold=self.bold,
                batch=dialog.batch, group=dialog.fg_group,
                stylesheet=dialog.stylesheet)
            self.width, self.height = self.label.get_size()

class Button(Control):
    """A button which can be pressed.  When released, generates an
    on_click callback."""
    def __init__(self, text, padding=4, on_click=None):
        Control.__init__(self)
        self.text = text
        self.button = None
        self.padding = padding
        self.is_pressed = False
        self.on_click = on_click

    def delete(self):
        Control.delete(self)
        if self.button is not None:
            self.button.delete()
            self.button = None

    def layout(self, x, y):
        self.x, self.y = x, y
        self.button.update(x, y, self.width, self.height)

    def on_gain_focus(self, dialog):
        Control.on_gain_focus(self, dialog)
        self.delete()
        dialog.needs_layout = True

    def on_gain_highlight(self, dialog):
        Control.on_gain_highlight(self, dialog)
        self.delete()
        dialog.needs_layout = True

    def on_lose_focus(self, dialog):
        Control.on_lose_focus(self, dialog)
        self.delete()
        dialog.needs_layout = True

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        self.delete()
        dialog.needs_layout = True

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        self.is_pressed = True
        self.delete()
        dialog.needs_layout = True

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        self.is_pressed = False
        self.delete()
        dialog.needs_layout = True
        if self.is_focus and self.on_click is not None:
            self.on_click(dialog, self)

    def size(self, dialog):
        if self.button is None:
            self.button = dialog.get_provider().get_button(
                text=self.text, padding=self.padding,
                is_pressed=self.is_pressed,
                is_highlight=self.is_highlight or self.is_focus,
                batch=dialog.batch,
                bg_group=dialog.bg_group,
                fg_group=dialog.fg_group,
                highlight_group=dialog.highlight_group,
                stylesheet=dialog.stylesheet)
        self.width, self.height = self.button.get_size()

class Input(Control):
    """A text input field."""
    def __init__(self, id=None, text="", length=20, padding=2):
        Control.__init__(self, cursor='text')
        self.id = id
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.length = length
        self.padding = padding
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
        if self.id is not None:
            dialog._set_value(self.id, self.get_text())
        Control.on_lose_focus(self, dialog)
        self.remove_highlight()
        if self.caret is not None:
            self.caret.visible = False
            self.caret.mark = self.caret.position = 0

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        self.remove_highlight()

    def on_mouse_drag(self, dialog, x, y, dx, dy, buttons, modifiers):
        self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        self.caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, dialog, text):
        self.caret.on_text(text)
        if self.id is not None:
            dialog._set_value(self.id, self.get_text())

    def on_text_motion(self, dialog, motion):
        self.caret.on_text_motion(motion)

    def on_text_motion_select(self, dialog, motion):
        self.caret.on_text_motion_select(motion)

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
            self.highlight = dialog.get_provider().get_text_field_highlight(
                self.width, self.height,
                color=dialog.stylesheet.highlight_color,
                batch=dialog.batch, group=dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def size(self, dialog):
        self.document.set_style(0, len(self.document.text),
                    dict(color=dialog.stylesheet.color,
                         font_size=dialog.stylesheet.font_size))

        # Calculate the needed size based on the font size
        font = self.document.get_font(0)
        glyphs = font.get_glyphs('A_')
        height = glyphs[0].height
        width = max([x.width for x in glyphs])
        self.width = self.length * width
        self.height = height + 2 * self.padding

        if self.id is not None:
            dialog._set_value(self.id, self.get_text())

        if self.text_layout is None:
            self.text_layout = pyglet.text.layout.IncrementalTextLayout(
                self.document,
                self.width - 2 * self.padding, self.height - 2 * self.padding,
                multiline=False,
                batch=dialog.batch, group=dialog.fg_group)
        if self.caret is None:
            self.caret = pyglet.text.caret.Caret(
                self.text_layout, color=dialog.stylesheet.color[0:3])
            self.caret.visible = False
        if self.field is None:
            self.field = dialog.get_provider().get_text_field(
                self.width, self.height, color=dialog.stylesheet.color,
                batch=dialog.batch, group=dialog.fg_group)
        if self.highlight is None and self.is_highlight:
            self.highlight = dialog.get_provider().get_text_field_highlight(
                self.width, self.height,
                color=dialog.stylesheet.highlight_color,
                batch=dialog.batch, group=dialog.highlight_group)

class MenuGroup(pyglet.graphics.Group):
    """
    For menus which have too many options to be shown on the screen at a time,
    we must restrict the display to a subset of the options.  The MenuGroup
    uses OpenGL's scissor test to crop any text beyond the limits of the menu.
    """
    def __init__(self, x, y, width, height, parent=None):
        pyglet.graphics.Group.__init__(self, parent)
        self.x, self.y, self.width, self.height = x, y, width, height

    def set_state(self):
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT | gl.GL_CURRENT_BIT)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(self.x, self.y, self.width, self.height)

    def unset_state(self):
        # gl.glDisable(gl.GL_SCISSOR_TEST)
        gl.glPopAttrib()

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

class Menu(Control):
    """
    The Menu displays a set of options and allows the user to select one.
    Only one option may be selected at a time, and an on_select callback will
    be sent, which usually results in the application removing the menu.

    If max_height is set and there are too many options to show at once,
    we will draw a border around the menu and a scrollbar on its right, which
    can be used to scroll the menu up and down.
    """
    def __init__(self, id=None, options=[], max_height=None,
                 align=layout.HALIGN_CENTER, spacing=2, padding=8,
                 always_border=False, on_select=None):
        Control.__init__(self)
        self.id = id
        self.options = options
        self.max_height = max_height
        self.needed_height = 0
        self.group = None
        self.align = align
        self.spacing = spacing
        self.padding = padding
        self.on_select = on_select
        self.labels = []
        self.highlight_index = -1
        self.select_index = -1
        self.labels_width = 0
        self.scrollbar = None
        self.always_border = always_border
        self.border = None
        self.dir = 0
        self.is_dragging = False

    def _get_index(self, x, y):
        index = -1
        if x >= self.x and x < self.x + self.labels_width and \
           y >= self.y and y < self.y + self.height:
            idx = 0
            for label in self.labels:
                if y >= label.y and y < label.y + label.height:
                    index = idx
                    break
                idx += 1
        return index

    def _layout_labels(self):
        top = self.y + self.height
        if self.scrollbar is not None:
            top += self.scrollbar.pos
        for label in self.labels:
            top -= label.height + self.spacing
            if self.align == layout.HALIGN_LEFT:
                label.update(self.x, top)
            elif self.align == layout.HALIGN_CENTER:
                label.update(self.x + self.labels_width/2 - label.width/2, top)
            else: # layout.HALIGN_RIGHT
                label.update(self.x + self.labels_width - label.width, top)

    def delete(self):
        for label in self.labels:
            label.delete()
        self.labels = []
        if self.scrollbar is not None:
            self.scrollbar.delete()
            self.scrollbar = None
        if self.border is not None:
            self.border.delete()
            self.border = None

    def layout(self, x, y):
        self.x, self.y = x, y
        if self.max_height is not None:
            self.group.x, self.group.y = x, y
        self._layout_labels()
        if self.scrollbar is not None:
            self.scrollbar.update(x + self.labels_width, y,
                                  self.max_height, self.needed_height)
        if self.border is not None:
            self.border.update(x, y, self.labels_width, self.height)

    def on_lose_focus(self, dialog):
        if self.is_dragging:
            self.is_dragging = False
        self.dir = 0

    def on_lose_highlight(self, dialog):
        self.set_highlight(dialog, -1)

    def on_mouse_drag(self, dialog, x, y, dx, dy, buttons, modifiers):
        if self.scrollbar is not None and self.is_dragging:
            self.scrollbar.drag(-dy)
            self._layout_labels()

    def on_mouse_motion(self, dialog, x, y, dx, dy):
        highlight_index = self._get_index(x, y)
        self.set_highlight(dialog, highlight_index)

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        if self.scrollbar is not None:
            if y >= self.y and y < self.y + self.height and \
               x > self.x + self.labels_width and x < self.x + self.width:
                # On the scrollbar, handle it
                if self.scrollbar.hit_up(x, y):
                    self.dir = -1
                    dialog.add_updatable(self)
                elif self.scrollbar.hit_down(x, y):
                    self.dir = 1
                    dialog.add_updatable(self)
                else:
                    self.scrollbar.set_bar_pos(x, y)
                    self._layout_labels()
                    self.is_dragging = True

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        if self.dir:
            dialog.remove_updatable(self)
            self.dir = 0
        select_index = self._get_index(x, y)
        if select_index == self.select_index:
            self.set_select(dialog, -1)
        else:
            self.set_select(dialog, select_index)

    def on_update(self, dialog, dt):
        if self.scrollbar is not None:
            self.scrollbar.drag(50 * self.dir * dt)
            self._layout_labels()

    def set_highlight(self, dialog, highlight_index):
        if self.highlight_index != highlight_index:
            if self.highlight_index >= 0:
                self.labels[self.highlight_index].set_highlight(dialog, False)
            if highlight_index >= 0:
                self.labels[highlight_index].set_highlight(dialog, True)
            self.highlight_index = highlight_index

    def set_options(self, dialog, options):
        dialog.needs_layout = True
        if self.id is not None:
            dialog._set_value(self.id, None)
        self.select_index = self.highlight_index = -1
        self.delete()
        self.options = options

    def set_select(self, dialog, select_index):
        if self.select_index != select_index:
            if self.select_index >= 0:
                self.labels[self.select_index].set_selected(dialog, False)
            if select_index >= 0:
                self.labels[select_index].set_selected(dialog, True)
            self.select_index = select_index
            if self.id is not None:
                if select_index >= 0:
                    dialog._set_value(self.id, self.options[select_index])
                else:
                    dialog._set_value(self.id, None)
            if self.on_select is not None:
                if select_index >= 0:
                    self.on_select(dialog, self, self.options[select_index])

    def size(self, dialog):
        if self.group is None:
            if self.max_height is not None:
                self.group = MenuGroup(0, 0, 0, self.max_height,
                                       parent=dialog.fg_group)
            else:
                self.group = dialog.fg_group
        if not self.labels:
            self.labels = [dialog.get_provider().get_menu_option(
                               option, padding=self.padding,
                               batch=dialog.batch, group=self.group,
                               stylesheet=dialog.stylesheet)
                           for option in self.options]
            if self.select_index >= 0:
                self.labels[self.select_index].set_selected(dialog, True)
            if self.highlight_index >= 0:
                self.labels[self.highlight_index].set_highlight(dialog, True)
            self.needed_height = reduce(lambda x, y: x + y + self.spacing,
                                 [x.height for x in self.labels]) \
                               + self.spacing
            self.labels_width = reduce(lambda x, y: max(x, y),
                                       [x.width for x in self.labels])
            self.width = self.labels_width
            if self.max_height is not None:
                self.group.width = self.labels_width
            self.height = self.needed_height
        if self.always_border or (self.max_height is not None and
                                  self.needed_height > self.max_height):
            if not self.border:
                self.border = dialog.get_provider().get_menu_border(
                    self.width, self.height, color=dialog.stylesheet.color,
                    batch=dialog.batch, group=dialog.fg_group)
        if self.max_height is not None and \
           self.needed_height > self.max_height:
            self.height = self.max_height
            if not self.scrollbar:
                # This may be confusing but:
                # max_height is the height of the bar
                # height is the total height needed to show everything
                self.scrollbar = dialog.get_provider().get_scrollbar(
                    self.height, self.needed_height, batch=dialog.batch,
                    group=dialog.fg_group, stylesheet=dialog.stylesheet)
                self.width = self.labels_width + self.scrollbar.width
        else:
            if self.scrollbar is not None:
                self.scrollbar.delete()
                self.scrollbar = None
