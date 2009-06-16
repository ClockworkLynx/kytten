# kytten/menu.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet

from widgets import Widget, Control
from dialog import Dialog
from frame import Frame
from layout import GetRelativePoint, VerticalLayout
from layout import ANCHOR_CENTER, ANCHOR_TOP_LEFT, ANCHOR_BOTTOM_LEFT
from layout import HALIGN_CENTER
from layout import VALIGN_TOP, VALIGN_CENTER, VALIGN_BOTTOM
from scrollable import Scrollable

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

    def delete(self):
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.background is not None:
            self.background.delete()
            self.background = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

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
        if self.label is not None:
            self.label.delete()
            self.label = None
        dialog.get_root().set_needs_layout()

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
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.background is not None:
            self.background.delete()
            self.background = None
        dialog.get_root().set_needs_layout()

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

    def get_value(self):
        return self.selected

    def is_input(self):
        return True

    def select(self, dialog, text):
        assert text in self.options
        if self.selected is not None:
            self.options[self.selected].unselect(dialog)
        self.selected = text
        menu_option = self.options[text]
        menu_option.select(dialog)

        if self.on_select is not None:
            self.on_select(text)

    def set_options(self, dialog, options):
        self.delete()
        self.selected = None
        menu_options = [MenuOption(option,
                                   anchor=(VALIGN_CENTER, self.align),
                                   menu=self) for option in options]
        self.options = dict(zip(options, menu_options))
        self.set(dialog, menu_options)
        dialog.get_root().set_needs_layout()

class Dropdown(Control):
    def __init__(self, options=[], selected=None, id=None,
                 max_height=400, align=VALIGN_TOP, on_select=None):
        assert options
        Control.__init__(self, id=id)
        self.options = options
        self.selected = selected or options[0]
        assert self.selected in self.options
        self.max_height = max_height
        self.align = align
        self.on_select = on_select

        self.field = None
        self.label = None
        self.pulldown_menu = None
        self.saved_dialog = None

    def _delete_pulldown_menu(self):
        if self.pulldown_menu is not None:
            self.pulldown_menu.delete()
            self.pulldown_menu.window.remove_handlers(self.pulldown_menu)
            self.pulldown_menu = None

    def delete(self):
        if self.field is not None:
            self.field.delete()
            self.field = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        self._delete_pulldown_menu()

    def get_value(self):
        return self.selected

    def is_input(self):
        return True

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        if self.pulldown_menu is not None:
            self._delete_pulldown_menu()  # if it's already up, close it
            return

        # Setup some callbacks for the dialog
        def on_escape(dialog):
            self._delete_pulldown_menu()

        def on_select(choice):
            self.selected = choice
            if self.label is not None:
                self.label.delete()
                self.label = None
            self._delete_pulldown_menu()
            self.saved_dialog.get_root().set_needs_layout()

            if self.on_select is not None:
                if self.id is not None:
                    self.on_select(self.id, choice)
                else:
                    self.on_select(choice)

        # We'll need the root window to get window size
        root_dialog = dialog.get_root()
        width, height = root_dialog.window.get_size()

        # Calculate the anchor point and location for the dialog
        if self.align == VALIGN_TOP:
            # Dropdown is at the top, pulldown appears below it
            anchor = ANCHOR_TOP_LEFT
            x = self.x
            y = -(height - self.y - 1)
        else:
            # Dropdown is at the bottom, pulldown appears above it
            anchor = ANCHOR_BOTTOM_LEFT
            x = self.x
            y = self.y + self.height + 1

        # Now to setup the dialog
        self.pulldown_menu = Dialog(
            Frame(
                Scrollable(Menu(options=self.options, on_select=on_select),
                           height=self.max_height),
                component='pulldown'
            ),
            window=root_dialog.window, batch=root_dialog.batch,
            group=root_dialog.root_group.parent, theme=root_dialog.theme,
            movable=False, anchor=anchor, offset=(x, y),
            on_escape=on_escape)
        root_dialog.window.push_handlers(self.pulldown_menu)

    def layout(self, x, y):
        Control.layout(self, x, y)

        self.field.update(x, y, self.width, self.height)
        x, y, width, height = self.field.get_content_region()

        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.label.x = x
        self.label.y = y - font.descent

    def set_options(self, dialog, options, selected=None):
        self.delete()
        self.options = options
        self.selected = selected or self.options[0]
        dialog.get_root().set_needs_layout()

    def size(self, dialog):
        self.saved_dialog = dialog  # save dialog for callback use

        if self.field is None:
            self.field = dialog.theme['dropdown']['image'].generate(
                dialog.theme['dropdown']['gui_color'],
                dialog.batch, dialog.bg_group)
        if self.label is None:
            self.label = pyglet.text.Label(self.selected,
                font_name=dialog.theme['dropdown']['font'],
                font_size=dialog.theme['dropdown']['font_size'],
                color=dialog.theme['dropdown']['text_color'],
                batch=dialog.batch, group=dialog.fg_group)
        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.width, self.height = self.field.get_needed_size(
            self.label.content_width, height)
