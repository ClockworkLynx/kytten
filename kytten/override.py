# kytten/override.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet

KYTTEN_LAYOUT_GROUPS = {}
KYTTEN_LAYOUT_GROUP_REFCOUNTS = {}

def GetKyttenLayoutGroups(group):
    if not KYTTEN_LAYOUT_GROUPS.has_key(group):
        top_group = pyglet.text.layout.TextLayoutGroup(group)
        background_group = pyglet.graphics.OrderedGroup(0, top_group)
        foreground_group = \
            pyglet.text.layout.TextLayoutForegroundGroup(1, top_group)
        foreground_decoration_group = \
            pyglet.text.layout.TextLayoutForegroundDecorationGroup(
                2, top_group)
        KYTTEN_LAYOUT_GROUPS[group] = (top_group,
                                       background_group,
                                       foreground_group,
                                       foreground_decoration_group)
        KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] = 0
    KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] += 1
    return KYTTEN_LAYOUT_GROUPS[group]

def ReleaseKyttenLayoutGroups(group):
    KYTTEN_LAYOUT_GROUP_REFCOUNTS[group] -= 1
    if not KYTTEN_LAYOUT_GROUP_REFCOUNTS[group]:
        del KYTTEN_LAYOUT_GROUP_REFCOUNTS[group]
        del KYTTEN_LAYOUT_GROUPS[group]

class KyttenLabel(pyglet.text.Label):
    def _init_groups(self, group):
        if not group:
            return # use the default groups
        self.top_group, self.background_group, self.foreground_group, \
            self.foreground_decoration_group = GetKyttenLayoutGroups(group)

    def teardown(self):
        pyglet.text.Label.teardown(self)
        group = self.top_group.parent
        if group is not None:
            ReleaseKyttenLayoutGroups(group)
            self.top_group = self.background_self = self.foreground_group \
                = self.foreground_decoration_group = None

class KyttenInputLabel(KyttenLabel):
    def _get_left(self):
        if self._multiline:
            width = self._width
        else:
            width = self.content_width
            if self.width and width > self.width:
                # align to right edge, clip left
                return self._x + self.width - width

        if self._anchor_x == 'left':
            return self._x
        elif self._anchor_x == 'center':
            return self._x - width // 2
        elif self._anchor_x == 'right':
            return self._x - width
        else:
            assert False, 'Invalid anchor_x'

    def _update(self):
        pyglet.text.Label._update(self)

        # Iterate through our vertex lists and break if we need to clip
        remove = []
        if self.width and not self._multiline:
            for vlist in self._vertex_lists:
                num_quads = len(vlist.vertices) / 8
                remove_quads = 0
                has_quads = False
                for n in xrange(0, num_quads):
                    x1, y1, x2, y2, x3, y3, x4, y4 = vlist.vertices[n*8:n*8+8]
                    tx1, ty1, tz1, tx2, ty2, tz2, \
                       tx3, ty3, tz3, tx4, ty4, tz4 = \
                       vlist.tex_coords[n*12:n*12+12]
                    if x2 >= self._x:
                        has_quads = True
                        m = n - remove_quads  # shift quads left
                        if x1 < self._x:  # clip on left side
                            percent = (float(self._x) - float(x1)) / \
                                      (float(x2) - float(x1))
                            x1 = x4 = max(self._x, x1)
                            tx1 = tx4 = (tx2 - tx1) * percent + tx1
                        vlist.vertices[m*8:m*8+8] = \
                            [x1, y1, x2, y2, x3, y3, x4, y4]
                        vlist.tex_coords[m*12:m*12+12] = \
                             [tx1, ty1, tz1, tx2, ty2, tz2,
                              tx3, ty3, tz3, tx4, ty4, tz4]
                    else:
                        # We'll delete quads entirely not visible
                        remove_quads = remove_quads + 1
                if remove_quads == num_quads:
                    remove.append(vlist)
                elif remove_quads > 0:
                    vlist.resize((num_quads - remove_quads) * 4)
        for vlist in remove:
            vlist.delete()
            self._vertex_lists.remove(vlist)

