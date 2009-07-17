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
from override import KyttenLabel
from scrollable import Scrollable

class MenuOption(Control):
    """
    MenuOption is a choice within a menu.  When selected, it inverts
    (inverted color against text-color background) to indicate that it
    has been chosen.
    """
    def __init__(self, text="", anchor=ANCHOR_CENTER, menu=None,
                 disabled=False):
        Control.__init__(self, disabled=disabled)
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

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        self.size(self.saved_dialog)  # to set up the highlight
        if self.highlight is not None:
            self.highlight.update(self.x, self.y,
                                  self.menu.width, self.height)

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_release(self, x, y, button, modifiers):
        self.menu.select(self.text)

    def select(self):
        if self.is_disabled():
            return  # disabled options can't be selected

        self.is_selected = True
        if self.label is not None:
            self.label.delete()
            self.label = None
        self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return
        Control.size(self, dialog)
        if self.is_selected:
            path = ['menuoption', 'selection']
        else:
            path = ['menuoption']
        if self.label is None:
            if self.is_disabled():
                color = dialog.theme[path]['disabled_color']
            else:
                color = dialog.theme[path]['text_color']
            self.label = KyttenLabel(self.text,
                color=color,
                font_name=dialog.theme[path]['font'],
                font_size=dialog.theme[path]['font_size'],
                batch=dialog.batch,
                group=dialog.fg_group)
            font = self.label.document.get_font()
            self.width = self.label.content_width
            self.height = font.ascent - font.descent

        if self.background is None:
            if self.is_selected:
                self.background = \
                    dialog.theme[path]['highlight']['image'].generate(
                        dialog.theme[path]['gui_color'],
                        dialog.batch,
                        dialog.bg_group)
        if self.highlight is None:
            if self.is_highlight():
                self.highlight = \
                    dialog.theme[path]['highlight']['image'].generate(
                        dialog.theme[path]['highlight_color'],
                        dialog.batch,
                        dialog.highlight_group)

    def unselect(self):
        self.is_selected = False
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.background is not None:
            self.background.delete()
            self.background = None
        self.saved_dialog.set_needs_layout()

    def teardown(self):
        self.menu = None
        Control.teardown(self)

class Menu(VerticalLayout):
    """
    Menu is a VerticalLayout of MenuOptions.  Moving the mouse across
    MenuOptions highlights them; clicking one selects it and causes Menu
    to send an on_click event.
    """
    def __init__(self, options=[], align=HALIGN_CENTER, padding=4,
                 on_select=None):
        self.align = align
        menu_options = self._make_options(options)
        self.options = dict(zip(options, menu_options))
        self.on_select = on_select
        self.selected = None
        VerticalLayout.__init__(self, menu_options,
                                align=align, padding=padding)

    def _make_options(self, options):
        menu_options = []
        for option in options:
            if option.startswith('-'):
                disabled = True
                option = option[1:]
            else:
                disabled = False
            menu_options.append(MenuOption(option,
                                           anchor=(VALIGN_CENTER, self.align),
                                           menu=self,
                                           disabled=disabled))
        return menu_options

    def get_value(self):
        return self.selected

    def is_input(self):
        return True

    def select(self, text):
        if not text in self.options:
            return

        if self.selected is not None:
            self.options[self.selected].unselect()
        self.selected = text
        menu_option = self.options[text]
        menu_option.select()

        if self.on_select is not None:
            self.on_select(text)

    def set_options(self, options):
        self.delete()
        self.selected = None
        menu_options = self._make_options(options)
        self.options = dict(zip(options, menu_options))
        self.set(menu_options)
        self.saved_dialog.set_needs_layout()

    def teardown(self):
        self.on_select = None
        VerticalLayout.teardown(self)

class Dropdown(Control):
    def __init__(self, options=[], selected=None, id=None,
                 max_height=400, align=VALIGN_TOP, on_select=None,
                 disabled=False):
        assert options
        Control.__init__(self, id=id, disabled=disabled)
        self.options = options
        self.selected = selected or options[0]
        assert self.selected in self.options
        self.max_height = max_height
        self.align = align
        self.on_select = on_select

        self.field = None
        self.label = None
        self.pulldown_menu = None

    def _delete_pulldown_menu(self):
        if self.pulldown_menu is not None:
            self.pulldown_menu.window.remove_handlers(self.pulldown_menu)
            self.pulldown_menu.teardown()
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

    def on_mouse_release(self, x, y, button, modifiers):
        if self.is_disabled():
            return

        if self.pulldown_menu is not None:
            self._delete_pulldown_menu()  # if it's already up, close it
            return

        # Setup some callbacks for the dialog
        root = self.saved_dialog.get_root()

        def on_escape(dialog):
            self._delete_pulldown_menu()

        def on_select(choice):
            self.selected = choice
            if self.label is not None:
                self.label.delete()
                self.label = None
            self._delete_pulldown_menu()
            self.saved_dialog.set_needs_layout()

            if self.on_select is not None:
                if self.id is not None:
                    self.on_select(self.id, choice)
                else:
                    self.on_select(choice)

        # We'll need the root window to get window size
        width, height = root.window.get_size()

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
                path=['dropdown', 'pulldown']
            ),
            window=root.window, batch=root.batch,
            group=root.root_group.parent, theme=root.theme,
            movable=False, anchor=anchor, offset=(x, y),
            on_escape=on_escape)
        root.window.push_handlers(self.pulldown_menu)

    def layout(self, x, y):
        Control.layout(self, x, y)

        self.field.update(x, y, self.width, self.height)
        x, y, width, height = self.field.get_content_region()

        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.label.x = x
        self.label.y = y - font.descent

    def set_options(self, options, selected=None):
        self.delete()
        self.options = options
        self.selected = selected or self.options[0]
        self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return
        Control.size(self, dialog)

        if self.is_disabled():
            color = dialog.theme['dropdown']['disabled_color']
        else:
            color = dialog.theme['dropdown']['gui_color']

        if self.field is None:
            self.field = dialog.theme['dropdown']['image'].generate(
                color,
                dialog.batch, dialog.bg_group)
        if self.label is None:
            self.label = KyttenLabel(self.selected,
                font_name=dialog.theme['dropdown']['font'],
                font_size=dialog.theme['dropdown']['font_size'],
                color=dialog.theme['dropdown']['text_color'],
                batch=dialog.batch, group=dialog.fg_group)
        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.width, self.height = self.field.get_needed_size(
            self.label.content_width, height)

    def teardown(self):
        self.on_select = False
        self._delete_pulldown_menu()
        Control.teardown(self)