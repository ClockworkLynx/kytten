# Copyright (c) 2009 Conrad "Lynx" Wong
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of DarkCoda nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""kytten - a skinnable, easily constructed GUI toolkit for pyglet

Inspired by simplui (Tristam MacDonald) and many other GUI projects.
Thanks to Gary Herron and Steve Johnson for debugging assistance!
"""

# GUI public constants

from layout import VALIGN_TOP, VALIGN_CENTER, VALIGN_BOTTOM
from layout import HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT
from layout import ANCHOR_TOP_LEFT, ANCHOR_TOP, ANCHOR_TOP_RIGHT, \
                   ANCHOR_LEFT, ANCHOR_CENTER, ANCHOR_RIGHT, \
                   ANCHOR_BOTTOM_LEFT, ANCHOR_BOTTOM, ANCHOR_BOTTOM_RIGHT

# GUI public classes

from button import Button
from checkbox import Checkbox
from dialog import Dialog, PopupMessage, PopupConfirm
from document import Document
from file_dialogs import FileLoadDialog, FileSaveDialog, DirectorySelectDialog
from frame import Frame, TitleFrame, Wrapper, SectionHeader, FoldingSection
from layout import GridLayout, HorizontalLayout, VerticalLayout, FreeLayout
from menu import Menu, Dropdown
from scrollable import Scrollable
from slider import Slider
from text_input import Input
from theme import Theme
from widgets import Widget, Spacer, Label
