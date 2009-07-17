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
