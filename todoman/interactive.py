import urwid

from todoman import widgets

_palette = [("error", "light red", "")]


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
        self._loop = None

        self._status = urwid.Text("")
        self._init_basic_fields()
        self._init_list_selector()
        self._init_help_text()

        save_btn = urwid.Button("Save", on_press=self._save)
        cancel_text = urwid.Text("Hit Ctrl-C to cancel, F1 for help.")
        buttons = urwid.Columns([(8, save_btn), cancel_text], dividechars=2)

        pile_items = []
        for label, field in [
            ("Summary", self._summary),
            ("Description", self._description),
            ("Location", self._location),
            ("Categories", self._categories),
            ("Start", self._dtstart),
            ("Due", self._due),
            ("Completed", self._completed),
            ("Priority", self._priority),
        ]:
            label = urwid.Text(label + ":", align="right")
            column = urwid.Columns([(13, label), field], dividechars=1)
            pile_items.append(("pack", column))

        grid = urwid.Pile(pile_items)
        spacer = urwid.Divider()

        self.left_column = urwid.ListBox(
            urwid.SimpleListWalker([grid, spacer, self._status, buttons])
        )
        right_column = urwid.ListBox(
            urwid.SimpleListWalker([urwid.Text("List:\n")] + self.list_selector)
        )

        self._ui = urwid.Columns([self.left_column, right_column])

    def _init_basic_fields(self):
        self._summary = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.todo.summary,
        )
        self._description = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.todo.description,
            multiline=True,
        )
        self._categories = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.formatter.format_categories(self.todo.categories),
        )
        self._location = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.todo.location,
        )
        self._due = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.formatter.format_datetime(self.todo.due),
        )
        self._dtstart = widgets.ExtendedEdit(
            parent=self,
            edit_text=self.formatter.format_datetime(self.todo.start),
        )
        self._completed = urwid.CheckBox("", state=self.todo.is_completed)
        self._priority = widgets.PrioritySelector(
            parent=self,
            priority=self.todo.priority,
            formatter_function=self.formatter.format_priority,
        )

    def _init_list_selector(self):
        self.list_selector = []
        for _list in self.lists:
            urwid.RadioButton(
                self.list_selector,
                _list.name,
                state=_list == self.current_list,
                on_state_change=self._change_current_list,
                user_data=_list,
            )

    def _init_help_text(self):
        self._help_text = urwid.Text(
            "\n\n"
            "Global:\n"
            " F1: Toggle help\n"
            " Ctrl-C: Cancel\n"
            " Ctrl-S: Save (only works if not a shell shortcut already)\n"
            "\n"
            "In Textfields:\n"
            + "\n".join(f" {k}: {v}" for k, v in widgets.ExtendedEdit.HELP)
            + "\n\nIn Priority Selector:\n"
            + "\n".join(f" {k}: {v}" for k, v in widgets.PrioritySelector.HELP)
        )

    def _change_current_list(self, radio_button, new_state, new_list):
        if new_state:
            self.current_list = new_list

    def _toggle_help(self):
        if self.left_column.body.contents[-1] is self._help_text:
            self.left_column.body.contents.pop()
        else:
            self.left_column.body.contents.append(self._help_text)
        self._loop.draw_screen()

    def set_status(self, text):
        self._status.set_text(text)

    def edit(self):
        """Shows the UI for editing a given todo."""
        self._loop = urwid.MainLoop(
            self._ui,
            palette=_palette,
            unhandled_input=self._keypress,
            handle_mouse=False,
        )
        try:
            self._loop.run()
        except KeyboardInterrupt:
            self._loop.stop()  # Try to leave terminal in usable state
        self._loop = None

    def _save(self, btn=None):
        try:
            self._save_inner()
        except Exception as e:
            self.set_status(("error", str(e)))
        else:
            raise urwid.ExitMainLoop()

    def _save_inner(self):
        self.todo.list = self.current_list
        self.todo.summary = self.summary
        self.todo.description = self.description
        self.todo.location = self.location
        self.todo.due = self.formatter.parse_datetime(self.due)
        self.todo.start = self.formatter.parse_datetime(self.dtstart)
        if not self.todo.is_completed and self._completed.get_state():
            self.todo.complete()
        elif self.todo.is_completed and not self._completed.get_state():
            self.todo.status = "NEEDS-ACTION"
            self.todo.completed_at = None
        self.todo.categories = [c.strip() for c in self.categories.split(",")]
        self.todo.priority = self.priority

        # TODO: categories
        # TODO: comment

        # https://tools.ietf.org/html/rfc5545#section-3.8
        # geo (lat, lon)
        # RESOURCE: the main room

    def _keypress(self, key):
        if key.lower() == "f1":
            self._toggle_help()
        elif key == "ctrl s":
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
    def categories(self):
        return self._categories.edit_text

    @property
    def priority(self):
        return self._priority.priority
