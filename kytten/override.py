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

    def _update(self):
        pyglet.text.Label._update(self)

        # Iterate through our vertex lists and break if we need to clip
        remove = []
        if self.width:
            right = self.x + self.width
            for vlist in self._vertex_lists:
                num_quads = len(vlist.vertices) / 8
                has_quads = False
                for n in xrange(0, num_quads):
                    x1, y1, x2, y2, x3, y3, x4, y4 = vlist.vertices[n*8:n*8+8]
                    if x1 < right:
                        has_quads = True
                        if x2 > right:
                            percent = (float(right) - float(x1)) / \
                                      (float(x2) - float(x1))
                            x3 = x2 = min(right, x2)
                            vlist.vertices[n*8:n*8+8] = \
                                [x1, y1, x2, y2, x3, y3, x4, y4]
                            tx1, ty1, tz1, tx2, ty2, tz2, \
                               tx3, ty3, tz3, tx4, ty4, tz4 = \
                               vlist.tex_coords[n*12:n*12+12]
                            tx3 = tx2 = (tx2 - tx1) * percent + tx1
                            vlist.tex_coords[n*12:n*12+12] = \
                                 [tx1, ty1, tz1, tx2, ty2, tz2,
                                  tx3, ty3, tz3, tx4, ty4, tz4]
                    else:
                        if n == 0:
                            remove.append(vlist)
                        else:
                            vlist.resize(n * 4)
                        break
        for vlist in remove:
            vlist.remove()
            self._vertex_lists.delete(vlist)

    def teardown(self):
        pyglet.text.Label.teardown(self)
        group = self.top_group.parent
        if group is not None:
            ReleaseKyttenLayoutGroups(group)
            self.top_group = self.background_self = self.foreground_group \
                = self.foreground_decoration_group = None
