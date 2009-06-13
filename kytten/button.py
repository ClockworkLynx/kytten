# kytten/button.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control

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
            self.delete()
            self.size(dialog)
            self.layout(self.x, self.y)

    def on_mouse_release(self, dialog, x, y, button, modifiers):
        if self.is_pressed:
            self.is_pressed = False

            # Delete the button to force it to be redrawn
            self.delete()
            self.size(dialog)
            self.layout(self.x, self.y)

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
                    dialog.theme['button']['gui_color'],
                    dialog.batch, dialog.bg_group)
            else:
                self.button = dialog.theme['button']['image'].generate(
                    dialog.theme['button']['gui_color'],
                    dialog.batch, dialog.bg_group)
        if self.highlight is None and self.is_highlight:
            self.highlight = dialog.theme['button']['image-highlight'].\
                generate(dialog.theme['button']['highlight_color'],
                         dialog.batch,
                         dialog.bg_group)
        if self.label is None:
            if self.is_pressed:
                button_type = 'down'
            else:
                button_type = 'up'
            self.label = pyglet.text.Label(self.text,
                font_name=dialog.theme['button'][button_type]['font'],
                font_size=dialog.theme['button'][button_type]['font_size'],
                color=dialog.theme['button'][button_type]['gui_color'],
                batch=dialog.batch, group=dialog.fg_group)

        # Treat the height of the label as ascent + descent
        font = self.label.document.get_font()
        height = font.ascent - font.descent # descent is negative
        self.width, self.height = self.button.get_needed_size(
            self.label.content_width, height)

