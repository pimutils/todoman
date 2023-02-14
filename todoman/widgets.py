# Copyright (c) 2016-2020 Hugo Osvaldo Barrera
# Copyright (c) 2013-2016 Christian Geier et al.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import re

import click
import urwid


class ExtendedEdit(urwid.Edit):
    """A text editing widget supporting some more editing commands"""

    HELP = [
        ("Ctrl-W", "Delete word"),
        ("Ctrl-U", "Delete until beginning of line"),
        ("Ctrl-K", "Delete until end of line"),
        ("Ctrl-A", "Go to beginning of line"),
        ("Ctrl-E", "Go to end of line"),
        ("Ctrl-D", "Delete forward letter"),
        ("Ctrl-O", "Edit in $EDITOR"),
    ]

    def __init__(self, parent, *a, **kw):
        self._parent = parent
        super().__init__(*a, **kw)

    def keypress(self, size, key):
        if key == "ctrl w":
            self._delete_word()
        elif key == "ctrl u":
            self._delete_till_beginning_of_line()
        elif key == "ctrl k":
            self._delete_till_end_of_line()
        elif key == "ctrl a":
            self._goto_beginning_of_line()
        elif key == "ctrl e":
            self._goto_end_of_line()
        elif key == "ctrl d":
            self._delete_forward_letter()
        elif key == "ctrl o":
            # Allow editing in $EDITOR
            self._editor()
        # TODO: alt b, alt f
        else:
            return super().keypress(size, key)

    def _delete_forward_letter(self):
        text = self.get_edit_text()
        pos = self.edit_pos
        text = text[:pos] + text[pos + 1 :]
        self.set_edit_text(text)

    def _delete_word(self):
        """delete word before cursor"""
        text = self.get_edit_text()
        t = text[: self.edit_pos].rstrip()

        words = re.findall(r"[\w]+|[^\w\s]", t, re.UNICODE)
        f_text = t if t == "" else t[: len(t) - len(words[-1])]

        self.set_edit_text(f_text + text[self.edit_pos :])
        self.set_edit_pos(len(f_text))

    def _delete_till_beginning_of_line(self):
        """delete till start of line before cursor"""
        text = self.get_edit_text()
        sol = text.rfind("\n", 0, self.edit_pos) + 1

        before_line = text[:sol]

        self.set_edit_text(before_line + text[self.edit_pos :])
        self.set_edit_pos(sol)

    def _delete_till_end_of_line(self):
        """delete till end of line before cursor"""
        text = self.get_edit_text()
        eol = text.find("\n", self.edit_pos)

        after_eol = "" if eol == -1 else text[eol:]

        self.set_edit_text(text[: self.edit_pos] + after_eol)

    def _goto_beginning_of_line(self):
        text = self.get_edit_text()
        sol = text.rfind("\n", 0, self.edit_pos) + 1
        self.set_edit_pos(sol)

    def _goto_end_of_line(self):
        text = self.get_edit_text()
        eol = text.find("\n", self.edit_pos)
        if eol == -1:
            eol = len(text)
        self.set_edit_pos(eol)

    def _editor(self):
        self._parent._loop.screen.clear()
        new_text = click.edit(self.get_edit_text())
        if new_text is not None:
            self.set_edit_text(new_text.strip())


class PrioritySelector(urwid.Button):
    HELP = [
        ("left", "Lower Priority"),
        ("right", "Higher Priority"),
    ]

    RANGES = [
        [0],
        [9, 8, 7, 6],
        [5],
        [1, 2, 3, 4],
    ]

    def __init__(self, parent, priority, formatter_function):
        self._parent = parent
        self._label = urwid.SelectableIcon("", 0)
        urwid.WidgetWrap.__init__(self, self._label)

        self._priority = priority
        self._formatter = formatter_function
        self._set_label()

    def _set_label(self):
        self.set_label(self._formatter(self._priority))

    def _update_label(self, delta=0):
        for i, r in enumerate(PrioritySelector.RANGES):
            if self._priority in r:
                self._priority = PrioritySelector.RANGES[
                    (i + delta) % len(PrioritySelector.RANGES)
                ][0]
                self._set_label()
                return

    def keypress(self, size, key):
        if key in ["right", "enter"]:
            self._update_label(1)
            return
        if key == "left":
            self._update_label(-1)
            return

        return super().keypress(size, key)

    @property
    def priority(self):
        return self._priority
