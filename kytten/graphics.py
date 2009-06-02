# kytten/graphics.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

"""
This module implements 'standard' graphic elements.  Currently this
has just a default graphic provider, but in the future it will include
the option to load a skin from an XML file and texture.

Graphics are distinct from widgets as follow:
* Widgets implement the control of GUI elements
* Graphics implement the display of GUI elements
"""

import pyglet
from pyglet import gl

def Color4(color):
    if len(color) == 4:
        return color
    else:
        return list(color) + [255]

class Stylesheet:
    """
    A container for common attributes used by many elements of the GUI.
    """
    def __init__(self, color=(255, 255, 255), inverse_color=(0, 0, 0),
                 highlight_color=(255, 235, 128, 64), font_size=12):
        """
        Defines a new stylesheet.

        @param color Color for text and GUI elements
        @param inverse_color Inverse of color, for highlighting a selection
        @param highlight_color Highlight color, used to brighten a selection
        @param font_size Size of font
        """
        self.color = Color4(color)
        self.inverse_color = Color4(inverse_color)
        self.highlight_color = Color4(highlight_color)
        self.font_size = font_size

DEFAULT_STYLESHEET = Stylesheet()
def GetDefaultStylesheet():
    """Returns the standard stylesheet."""
    global DEFAULT_STYLESHEET
    return DEFAULT_STYLESHEET

class Border:
    """A simple outline."""

    def __init__(self, width, height, color, batch=None, group=None):
        self.width = width
        self.height = height
        self.color = color
        self.x = self.y = 0
        self.batch = batch
        self.group = group
        self.vertex_list = batch.add(8, gl.GL_LINES, group,
            ('v2i', self._get_vertices()),
            ('c4B', color * 8))

    def _get_vertices(self):
        x1, y1 = self.x, self.y
        x2, y2 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1,
                x2, y1, x2, y2,
                x2, y2, x1, y2,
                x1, y2, x1, y1)

    def delete(self):
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def get_size(self):
        return self.width, self.height

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.vertex_list.vertices = self._get_vertices()

class Rectangle:
    """A simple solid-colored rectangle."""

    def __init__(self, width, height, color, batch=None, group=None):
        self.width = width
        self.height = height
        self.color = color
        self.x = self.y = 0
        self.batch = batch
        self.group = group
        self.vertex_list = batch.add(4, gl.GL_QUADS, group,
            ('v2i', self._get_vertices()),
            ('c4B', color * 4))

    def _get_vertices(self):
        x1, y1 = self.x, self.y
        x2, y2 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def delete(self):
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def get_size(self):
        return self.width, self.height

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.vertex_list.vertices = self._get_vertices()

class PanelGraphicElement:
    """
    A 9-patch style texture.  We don't extract sizing information from
    the texture like 9-patch, we require margins to be passed in as parameters.
    """
    def __init__(self, texture, batch, group,
                 left=0, right=0, top=0, bottom=0, color=(255, 255, 255)):
        assert batch is not None and group is not None
        self.margins = (left, right, top, bottom)
        self.x = self.y = 0
        self.width, self.height = texture.width, texture.height

        # We calculate the inner texture to get tex_coords for the inside.
        self.outer_texture = texture
        self.inner_texture = texture.get_region(
            left, bottom,
            texture.width - right - left,
            texture.height - top - bottom).get_texture()

        # The entire panel can be drawn as a single vertex list, since
        # it's all from the same texture.
        self.group = pyglet.graphics.TextureGroup(texture, group)
        self.vertex_list = batch.add(36, gl.GL_QUADS, self.group,
            ('v2i', self._get_vertices()),
            ('c%dB' % len(color), color * 36),
            ('t2f', self._get_tex_coords()))

    def _get_tex_coords(self):
        x1, y1 = self.outer_texture.tex_coords[0:2] # outer's lower left
        x4, y4 = self.outer_texture.tex_coords[6:8] # outer's upper right
        x2, y2 = self.inner_texture.tex_coords[0:2] # inner's lower left
        x3, y3 = self.inner_texture.tex_coords[6:8] # inner's upper right
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def _get_vertices(self):
        left, right, top, bottom = self.margins
        x1, y1 = self.x, self.y
        x2, y2 = x1 + left, y1 + bottom
        x3, y3 = x1 + self.width - right, y1 + self.height - top
        x4, y4 = x1 + self.width, y1 + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2,  # bottom left
                x2, y1, x3, y1, x3, y2, x2, y2,  # bottom
                x3, y1, x4, y1, x4, y2, x3, y2,  # bottom right
                x1, y2, x2, y2, x2, y3, x1, y3,  # left
                x2, y2, x3, y2, x3, y3, x2, y3,  # center
                x3, y2, x4, y2, x4, y3, x3, y3,  # right
                x1, y3, x2, y3, x2, y4, x1, y4,  # top left
                x2, y3, x3, y3, x3, y4, x2, y4,  # top
                x3, y3, x4, y3, x4, y4, x3, y4)  # top right

    def delete(self):
        if self.vertex_list is not None:
            self.vertex_list.delete()
            self.vertex_list = None

    def get_margins(self):
        return self.margins

    def update(self, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.vertex_list.vertices = self._get_vertices()

class ButtonGraphicElement:
    """Depicts a button in one state.  We recreate the button when we
    change its state.

    TODO(lynx): change this to accept several texture regions and simply
    switch which tex_coords we use depending on whether the button is
    pressed or not."""
    def __init__(self, panel, label, highlight, padding=4):
        self.panel = panel
        self.label = label
        self.highlight = highlight
        self.padding = padding

    def delete(self):
        if self.panel is not None:
            self.panel.delete()
            self.panel = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def get_size(self):
        left, right, top, bottom = self.panel.get_margins()
        return (self.label.content_width + left + right + 2 * self.padding,
                self.label.content_height + top + bottom + 2 * self.padding)

    def update(self, x, y, width, height):
        if self.panel is not None:
            self.panel.update(x, y, width, height)
        if self.highlight is not None:
            self.highlight.update(x, y, width, height)
        if self.label is not None:
            left, right, top, bottom = self.panel.get_margins()
            self.label.x = x + left + self.padding
            self.label.y = y + bottom + self.padding

class Text:
    """A wrapper around Label to fit it into our graphics management."""
    def __init__(self, text, bold=False, batch=None, group=None,
                 stylesheet=GetDefaultStylesheet()):
        self.label = pyglet.text.Label(text,
                                       batch=batch, group=group,
                                       bold=bold,
                                       font_size=stylesheet.font_size,
                                       color=stylesheet.color,
                                       anchor_y='bottom')
        self.x = self.y = 0
        self.width = self.label.content_width
        self.height = self.label.content_height

    def delete(self):
        if self.label is not None:
            self.label.delete()
            self.label = None

    def get_size(self):
        if self.label is not None:
            return (self.label.content_width, self.label.content_height)
        else:
            return (0, 0)

    def set_bold(self, bold=True):
        self.label.bold = bold

    def set_color(self, color):
        self.label.color = color

    def update(self, x, y):
        self.x, self.y = x, y
        self.label.x, self.label.y = x, y

class MenuOption(Text):
    """Menu options are smarter than ordinary text in that they can be
    highlighted or selected.  A highlighted menu option has a highlight
    rectangle drawn on top; a selected menu option is drawn in reverse
    colors."""
    def __init__(self, text="", padding=8, batch=None, group=None,
                 stylesheet=GetDefaultStylesheet()):
        Text.__init__(self, text, batch=batch, group=group,
                      stylesheet=stylesheet)
        self.padding = padding
        self.width = self.width + 2 * self.padding
        self.background = None
        self.highlight = None

    def delete(self):
        if self.background is not None:
            self.background.delete()
            self.background = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None
        Text.delete(self)

    def get_size(self):
        return self.width, self.height

    def set_highlight(self, dialog, highlight=True):
        if (self.highlight and highlight) or \
           (self.highlight is None and not highlight):
            return # no need to change the state of things
        if highlight:
            self.highlight = dialog.get_provider().get_text_field_highlight(
                    self.width, self.height,
                    color=dialog.stylesheet.highlight_color,
                    batch=dialog.batch, group=dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)
        else:
            self.highlight.delete()
            self.highlight = None

    def set_selected(self, dialog, selected=True):
        if (self.background and selected) or \
           (self.background is None and not selected):
            return # no need to change the state of things
        if selected:
            self.background = dialog.get_provider().get_selection_background(
                self.width, self.height,
                color=dialog.stylesheet.color,
                batch=dialog.batch, group=dialog.bg_group)
            Text.set_color(self, dialog.stylesheet.inverse_color)
            self.background.update(self.x, self.y, self.width, self.height)
        else:
            self.background.delete()
            self.background = None
            Text.set_color(self, dialog.stylesheet.color)

    def update(self, x, y):
        Text.update(self, x + self.padding, y)
        self.x, self.y = x, y
        if self.background is not None:
            self.background.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

class Scrollbar:
    """
    The scrollbar, attached to a menu or layout, can be slid from 0 (top)
    to max_height to allow the entire menu to be viewed.

    The scrollbar expects its textures to all be drawn from the same skin
    texture file.
    """
    def __init__(self, height, max_height,
                 base_texture, up_texture, space_texture,
                 down_texture, up_max_texture, bar_top_texture,
                 bar_middle_texture, bar_bottom_texture, down_max_texture,
                 color=(255, 255, 255, 255),
                 batch=None, group=None):
        assert height >= up_texture.height + space_texture.height + \
               down_texture.height
        self.x = self.y = 0
        self.pos = 0
        self.max_pos = max(max_height - height, 0)
        self.height = height
        self.width = space_texture.width
        self.max_height = max_height
        self.texture = base_texture
        self.up_texture = up_texture
        self.space_texture = space_texture
        self.down_texture = down_texture
        self.up_max_texture = up_max_texture
        self.bar_top_texture = bar_top_texture
        self.bar_middle_texture = bar_middle_texture
        self.bar_bottom_texture = bar_bottom_texture
        self.down_max_texture = down_max_texture
        self.root_group = pyglet.graphics.TextureGroup(base_texture, group)
        self.bg_group = pyglet.graphics.OrderedGroup(0, self.root_group)
        self.fg_group = pyglet.graphics.OrderedGroup(1, self.root_group)
        self.highlight_group = pyglet.graphics.OrderedGroup(2, self.root_group)
        self.up_vertex_list = batch.add(4, gl.GL_QUADS, self.fg_group,
            ('v2i', self._get_up_vertices()),
            ('c4B', color * 4),
            ('t3f', up_max_texture.tex_coords))
        self.down_vertex_list = batch.add(4, gl.GL_QUADS, self.fg_group,
            ('v2i', self._get_down_vertices()),
            ('c4B', color * 4),
            ('t3f', down_texture.tex_coords))
        self.bg_vertex_list = batch.add(4, gl.GL_QUADS, self.bg_group,
            ('v2i', self._get_bg_vertices()),
            ('c4B', color * 4),
            ('t3f', space_texture.tex_coords))
        self.bar_vertex_list = batch.add(12, gl.GL_QUADS, self.fg_group,
            ('v2i', self._get_bar_vertices()),
            ('c4B', color * 12),
            ('t3f', bar_top_texture.tex_coords +
                    bar_middle_texture.tex_coords +
                    bar_bottom_texture.tex_coords))

    def _get_bar_vertices(self):
        bg_bottom = self.y + self.down_texture.height
        bg_top = self.y + self.height - self.up_texture.height
        bg_height = bg_top - bg_bottom
        bar_height = bg_height * self.height / self.max_height
        bar_offset = int(self.pos * (bg_height - bar_height) / self.max_pos)
        xR, y4 = self.x + self.width, bg_top - bar_offset
        xL, y1 = self.x, y4 - bar_height
        y3 = y4 - self.bar_top_texture.height
        y2 = y1 + self.bar_bottom_texture.height
        return (xL, y3, xR, y3, xR, y4, xL, y4,  # top
                xL, y2, xR, y2, xR, y3, xL, y3,  # middle
                xL, y1, xR, y1, xR, y2, xL, y2)  # bottom

    def _get_bg_vertices(self):
        x1, y1 = self.x, self.y + self.down_texture.height
        x2 = self.x + self.width
        y2 = self.y + self.height - self.up_texture.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def _get_down_vertices(self):
        x1, y1 = self.x, self.y
        x2 = self.x + self.width
        y2 = self.y + self.down_texture.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def _get_up_vertices(self):
        x1, y1 = self.x, self.y + self.height - self.up_texture.height
        x2 = self.x + self.width
        y2 = self.y + self.height
        return (x1, y1, x2, y1, x2, y2, x1, y2)

    def _set_bar_pos(self, pos):
        self.bar_vertex_list.vertices = self._get_bar_vertices()
        if pos <= 0:
            self.up_vertex_list.tex_coords = self.up_max_texture.tex_coords
        else:
            self.up_vertex_list.tex_coords = self.up_texture.tex_coords
        if pos >= self.max_pos:
            self.down_vertex_list.tex_coords = self.down_max_texture.tex_coords
        else:
            self.down_vertex_list.tex_coords = self.down_texture.tex_coords
        pos = min(pos, self.max_pos)
        pos = max(pos, 0)
        self.pos = pos
        self.bar_vertex_list.vertices = self._get_bar_vertices()

    def delete(self):
        if self.up_vertex_list is not None:
            self.up_vertex_list.delete()
            self.up_vertex_list = None
        if self.down_vertex_list is not None:
            self.down_vertex_list.delete()
            self.down_vertex_list = None
        if self.bg_vertex_list is not None:
            self.bg_vertex_list.delete()
            self.bg_vertex_list = None
        if self.bar_vertex_list is not None:
            self.bar_vertex_list.delete()
            self.bar_vertex_list = None

    def drag(self, dy):
        pos = self.pos + dy * self.max_height / self.height
        self._set_bar_pos(pos)

    def hit_down(self, x, y):
        x1, y1 = self.x, self.y
        x2 = self.x + self.width
        y2 = self.y + self.down_texture.height
        return x >= x1 and x < x2 and y >= y1 and y < y2

    def hit_up(self, x, y):
        x1, y1 = self.x, self.y + self.height - self.up_texture.height
        x2 = self.x + self.width
        y2 = self.y + self.height
        return x >= x1 and x < x2 and y >= y1 and y < y2

    def set_bar_pos(self, x, y):
        bg_bottom = self.y + self.down_texture.height
        bg_top = self.y + self.height - self.up_texture.height
        bg_height = bg_top - bg_bottom
        bar_height = bg_height * self.height / self.max_height
        bar_offset = self.pos * (bg_height - bar_height) / self.max_pos
        xR, y4 = self.x + self.width, bg_top - bar_offset
        xL, y1 = self.x, y4 - bar_height
        if y > y4:
            # Position the top of the bar to hit the mouse
            pos = (bg_top - y) * self.max_pos / (bg_height - bar_height)
        elif y < y1:
            # Position the bottom of the bar to hit the mouse
            pos = (bg_top - y - bar_height) * self.max_pos / \
                (bg_height - bar_height)
        else:
            return # No change to position
        self._set_bar_pos(pos)

    def update(self, x, y, height, max_height):
        self.x, self.y = x, y
        self.height, self.max_height = height, max_height
        self.up_vertex_list.vertices = self._get_up_vertices()
        self.down_vertex_list.vertices = self._get_down_vertices()
        self.bg_vertex_list.vertices = self._get_bg_vertices()
        self.bar_vertex_list.vertices = self._get_bar_vertices()

class DefaultGraphicElementProvider:
    """
    This is a hardcoded graphic provider which expects a few selected files
    and passes set parameters to the graphic elements it recognizes.

    TODO(lynx): replace this with a provider which reads an XML file and
    a skin image file.
    """
    def __init__(self):
        self.atlas = pyglet.image.atlas.TextureBin()

        # Load the atlas with our textures
        self.panel_texture = self.atlas.add(pyglet.image.load('panel.png'))
        self.button_up_texture = self.atlas.add(pyglet.image.load(
            'button-up.png'))
        self.button_down_texture = self.atlas.add(pyglet.image.load(
            'button-down.png'))
        self.button_highlight_texture = self.atlas.add(pyglet.image.load(
            'button-highlight.png'))

        # The scrollbar is a single 16x96 image that we break up into pieces
        self.scrollbar_texture = self.atlas.add(pyglet.image.load(
            'scrollbar.png'))
        self.scrollbar_up_texture = self.scrollbar_texture.get_region(
            0, 80, 16, 16).get_texture()
        self.scrollbar_space_texture = self.scrollbar_texture.get_region(
            0, 64, 16, 16).get_texture()
        self.scrollbar_down_texture = self.scrollbar_texture.get_region(
            0, 48, 16, 16).get_texture()
        self.scrollbar_up_max_texture = self.scrollbar_texture.get_region(
            0, 32, 16, 16).get_texture()
        self.scrollbar_bar_top_texture = self.scrollbar_texture.get_region(
            0, 26, 16, 6).get_texture()
        self.scrollbar_bar_middle_texture = self.scrollbar_texture.get_region(
            0, 22, 16, 4).get_texture()
        self.scrollbar_bar_bottom_texture = self.scrollbar_texture.get_region(
            0, 16, 16, 6).get_texture()
        self.scrollbar_down_max_texture = self.scrollbar_texture.get_region(
            0, 0, 16, 16).get_texture()

    def get_button(self, text="", is_pressed=False, is_highlight=False,
                   batch=None, bg_group=None, fg_group=None,
                   highlight_group=None,
                   stylesheet=GetDefaultStylesheet(),
                   padding=4):
        if is_pressed:
            panel = PanelGraphicElement(
                self.button_down_texture, batch, bg_group,
                left=10, right=10, top=10, bottom=10, color=stylesheet.color)
            label = pyglet.text.Label(text, batch=batch, group=fg_group,
                                      font_size=stylesheet.font_size,
                                      color=stylesheet.inverse_color,
                                      anchor_y='bottom')
        else:
            panel = PanelGraphicElement(
                self.button_up_texture, batch, bg_group,
                left=10, right=10, top=10, bottom=10, color=stylesheet.color)
            label = pyglet.text.Label(text, batch=batch, group=fg_group,
                                      font_size=stylesheet.font_size,
                                      color=stylesheet.color,
                                      anchor_y='bottom')
        if is_highlight:
            highlight = PanelGraphicElement(
                self.button_highlight_texture, batch, highlight_group,
                left=10, right=10, top=10, bottom=10,
                color=stylesheet.highlight_color)
        else:
            highlight = None
        return ButtonGraphicElement(panel, label, highlight, padding=padding)

    def get_panel(self, batch=None, group=None, color=(255, 255, 255)):
        return PanelGraphicElement(self.panel_texture, batch, group,
                                   left=16, right=16, top=16, bottom=16,
                                   color=color)

    def get_selection_background(self, width, height,
                                 color=(255, 235, 128, 128),
                                 batch=None, group=None):
        return Rectangle(width, height, Color4(color),
                         batch=batch, group=group)

    def get_text(self, text="", batch=None, group=None, bold=False,
                 stylesheet=GetDefaultStylesheet()):
        return Text(text, bold=bold, batch=batch, group=group,
                    stylesheet=stylesheet)

    def get_text_field(self, width, height, color=(255, 255, 255),
                       batch=None, group=None):
        return Border(width, height, Color4(color),
                         batch=batch, group=group)

    def get_text_field_highlight(self, width, height,
                                 color=(255, 235, 128, 128),
                                 batch=None, group=None):
        return Rectangle(width, height, Color4(color),
                         batch=batch, group=group)

    def get_menu_option(self, text="", padding=8, batch=None, group=None,
                        stylesheet=GetDefaultStylesheet()):
        return MenuOption(text, padding=padding, batch=batch, group=group,
                          stylesheet=stylesheet)

    def get_menu_border(self, width, height, color=(255, 255, 255),
                        batch=None, group=None):
        return Border(width, height, Color4(color), batch=batch, group=group)

    def get_scrollbar(self, height, max_height, batch=None, group=None,
                      stylesheet=GetDefaultStylesheet()):
        return Scrollbar(height, max_height,
                         self.scrollbar_texture,
                         self.scrollbar_up_texture,
                         self.scrollbar_space_texture,
                         self.scrollbar_down_texture,
                         self.scrollbar_up_max_texture,
                         self.scrollbar_bar_top_texture,
                         self.scrollbar_bar_middle_texture,
                         self.scrollbar_bar_bottom_texture,
                         self.scrollbar_down_max_texture,
                         color=stylesheet.color,
                         batch=batch, group=group)

DEFAULT_GRAPHIC_ELEMENT_PROVIDER = None

def GetDefaultGraphicElementProvider():
    global DEFAULT_GRAPHIC_ELEMENT_PROVIDER
    if DEFAULT_GRAPHIC_ELEMENT_PROVIDER is None:
        DEFAULT_GRAPHIC_ELEMENT_PROVIDER = DefaultGraphicElementProvider()
    return DEFAULT_GRAPHIC_ELEMENT_PROVIDER
