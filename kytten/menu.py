# kytten/menu.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet

from widgets import Widget, Control
from layout import GetRelativePoint, VerticalLayout
from layout import ANCHOR_CENTER, HALIGN_CENTER, VALIGN_CENTER

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
                    color=dialog.theme['menuoption']
                                      ['selection']
                                      ['text_color'],
                    font_name=dialog.theme['font'],
                    font_size=dialog.theme['font_size'],
                    batch=dialog.batch,
                    group=dialog.fg_group)
            else:
                self.label = pyglet.text.Label(self.text,
                    color=dialog.theme['menuoption']['text_color'],
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
                        generate(dialog.theme['menuoption']
                                             ['selection']
                                             ['gui_color'],
                                 dialog.batch,
                                 dialog.bg_group)
        if self.highlight is None:
            if self.is_highlight:
                self.highlight = \
                    dialog.theme['menuoption']['image-highlight'].\
                        generate(dialog.theme['menuoption']['highlight_color'],
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

