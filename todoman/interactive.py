import urwid

from todoman import widgets

_palette = [
    ('error', 'light red', '')
]


class EditState:
    none = object()
    saved = object()


class TodoEditor:
    """
    The UI for a single todo entry.
    """

    def __init__(self, todo, lists, formatter):
        """
        :param model.Todo todo: The todo object which will be edited.
        """
        self.current_list = todo.list
        self.todo = todo
        self.lists = list(lists)
        self.formatter = formatter
        self.saved = EditState.none
        self._loop = None

        self._msg_text = urwid.Text('')

        due = formatter.format_datetime(todo.due) or ''
        dtstart = formatter.format_datetime(todo.start) or ''
        priority = formatter.format_priority(todo.priority)

        self._summary = widgets.ExtendedEdit(parent=self,
                                             edit_text=todo.summary)
        self._description = widgets.ExtendedEdit(
            parent=self,
            edit_text=todo.description,
            multiline=True,
        )
        self._location = widgets.ExtendedEdit(
            parent=self,
            edit_text=todo.location
        )
        self._due = widgets.ExtendedEdit(parent=self, edit_text=due)
        self._dtstart = widgets.ExtendedEdit(parent=self, edit_text=dtstart)
        self._completed = urwid.CheckBox("", state=todo.is_completed)
        self._priority = widgets.ExtendedEdit(parent=self, edit_text=priority)

        save_btn = urwid.Button('Save', on_press=self._save)
        cancel_text = urwid.Text('Hit Ctrl-C to cancel, F1 for help.')
        buttons = urwid.Columns([(8, save_btn), cancel_text], dividechars=2)

        pile_items = []
        for label, field in [("Summary", self._summary),
                             ("Description", self._description),
                             ("Location", self._location),
                             ("Due", self._due),
                             ("Start", self._dtstart),
                             ("Completed", self._completed),
                             ("Priority", self._priority),
                             ]:
            label = urwid.Text(label + ":", align='right')
            column = urwid.Columns([(13, label), field], dividechars=1)
            pile_items.append(('pack', column))

        grid = urwid.Pile(pile_items)
        spacer = urwid.Divider()

        self._ui_content = items = [grid, spacer, self._msg_text, buttons]
        left_column = urwid.ListBox(items)

        self._help_text = urwid.Text(
            '\n\nGlobal:\n'
            ' F1: Toggle help\n'
            ' Ctrl-C: Cancel\n'
            ' Ctrl-S: Save (only works if not a shell shortcut already)\n\n'
            'In Textfields:\n'
            + '\n'.join(' {}: {}'.format(k, v) for k, v
                        in widgets.ExtendedEdit.HELP)
        )

        list_selector = []
        for _list in self.lists:
            urwid.RadioButton(
                list_selector,
                _list.name,
                state=_list == self.current_list,
                on_state_change=self._change_current_list,
                user_data=_list,
            )
        right_column = urwid.ListBox([urwid.Text('List:\n')] + list_selector)

        self._ui = urwid.Columns([left_column, right_column])

    def _change_current_list(self, radio_button, new_state, new_list):
        if new_state:
            self.current_list = new_list

    def _toggle_help(self):
        if self._ui_content[-1] is self._help_text:
            self._ui_content.pop()
        else:
            self._ui_content.append(self._help_text)
        self._loop.draw_screen()

    def message(self, text):
        self._msg_text.set_text(text)

    def edit(self):
        """
        Shows the UI for editing a given todo. Returns True if modifications
        were saved.
        """
        self._loop = urwid.MainLoop(
            self._ui,
            palette=_palette,
            unhandled_input=self._keypress,
            handle_mouse=False,
        )
        try:
            self._loop.run()
        except Exception:
            try:  # Try to leave terminal in usable state
                self._loop.stop()
            except Exception:
                pass
            raise
        self._loop = None
        return self.saved

    def _save(self, btn=None):
        try:
            self._save_inner()
        except Exception as e:
            self.message(('error', str(e)))
        else:
            self.saved = EditState.saved
            raise urwid.ExitMainLoop()

    def _save_inner(self):
        self.todo.list = self.current_list
        self.todo.summary = self.summary
        self.todo.description = self.description
        self.todo.location = self.location
        self.todo.due = self.formatter.parse_datetime(self.due)
        self.todo.start = self.formatter.parse_datetime(self.dtstart)

        self.todo.is_completed = self._completed.get_state()

        self.todo.priority = self.formatter.parse_priority(self.priority)

        # TODO: categories
        # TODO: comment
        # TODO: priority (0: undef. 1: max, 9: min)

        # https://tools.ietf.org/html/rfc5545#section-3.8
        # geo (lat, lon)
        # RESOURCE: the main room

    def _cancel(self, btn):
        raise urwid.ExitMainLoop()

    def _keypress(self, key):
        if key.lower() == 'f1':
            self._toggle_help()
        elif key == 'ctrl s':
            self._save()

    @property
    def summary(self):
        return self._summary.edit_text

    @property
    def description(self):
        return self._description.edit_text

    @property
    def location(self):
        return self._location.edit_text

    @property
    def due(self):
        return self._due.edit_text

    @property
    def dtstart(self):
        return self._dtstart.edit_text

    @property
    def priority(self):
        return self._priority.edit_text
