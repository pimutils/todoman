from datetime import datetime

import urwid
from dateutil.tz import tzlocal


class TodoEditor:
    """
    The UI for a single todo entry.
    """

    def __init__(self, todo, formatter):
        """
        :param model.Todo todo: The todo object which will be edited.
        """

        self.todo = todo
        self.formatter = formatter
        self.saved = False

        if todo.due:
            # TODO: use proper date_format
            due = formatter.format_date(todo.due)
        else:
            due = ""

        self._summary = urwid.Edit(edit_text=todo.summary)
        self._description = urwid.Edit(edit_text=todo.description,
                                       multiline=True)
        self._location = urwid.Edit(edit_text=todo.location)
        self._due = urwid.Edit(edit_text=due)
        self._completed = urwid.CheckBox("", state=todo.completed is not None)
        self._urgent = urwid.CheckBox("", state=todo.priority not in [None, 0])

        save_btn = urwid.Button('Save', on_press=self._save)
        cancel_btn = urwid.Button('Cancel', on_press=self._cancel)
        buttons = urwid.Columns([(10, cancel_btn), (8, save_btn)],
                                dividechars=2)

        pile_items = []
        for label, field in [("Summary", self._summary),
                             ("Description", self._description),
                             ("Location", self._location),
                             ("Due", self._due),
                             ("Completed", self._completed),
                             ("Urgent", self._urgent),
                             ]:
            label = urwid.Text(label + ":", align='right')
            column = urwid.Columns([(13, label), field], dividechars=1)
            pile_items.append(('pack', column))

        grid = urwid.Pile(pile_items)
        spacer = urwid.Divider()

        items = [grid, spacer, buttons]

        self._ui = urwid.ListBox(items)

    def edit(self):
        """
        Shows the UI for editing a given todo. Returns True if modifications
        were saved.
        """
        loop = urwid.MainLoop(self._ui, unhandled_input=self._keypress)
        loop.run()
        return self.saved

    def _save(self, btn):
        self.todo.summary = self.summary
        self.todo.description = self.description
        self.todo.location = self.location
        if self.due:
            self.todo.due = self.formatter.unformat_date(self.due)
        else:
            self.todo.due = None

        if not self.todo.completed and self._completed.get_state():
            self.todo.complete()
        elif self.todo.completed and not self._completed.get_state():
            self.todo.undo()

        # If it was already non-zero, keep it that way. Let's not overwrite
        # values 1 thru 8.
        if self._urgent.get_state() and not self.todo.priority:
            self.todo.priority = 9
        else:
            self.todo.priority = 0

        # TODO: categories
        # TODO: comment
        # TODO: priority (0: undef. 1: max, 9: min)

        # https://tools.ietf.org/html/rfc5545#section-3.8
        # geo (lat, lon)
        # RESOURCE: the main room

        self.saved = True
        raise urwid.ExitMainLoop()

    def _cancel(self, btn):
        raise urwid.ExitMainLoop()

    def _keypress(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

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


class TodoFormatter:

    # This one looks good with [X]
    compact_format = "[{completed}] {urgent} {due} {summary} ({percent}%)"
    # compact_format = "{completed} {urgent}  {due}  {summary}"
    detailed_format = """\
{summary}
{due}{done}{urgent}

{description}"""

    def __init__(self, date_format):
        self.date_format = date_format
        self.empty_date = " " * len(self.format_date(datetime.now()))
        self._localtimezone = tzlocal()

    def compact(self, todo):
        """
        Returns a brief representation of a task, suitable for displaying
        on-per-line.

        :param Todo todo: The todo component.
        """
        # completed = "✓" if todo.percent_complete == 100 else " "
        completed = "X" if todo.percent_complete == 100 else " "
        percent = todo.percent_complete
        urgent = " " if todo.priority in [None, 0] else "!"
        due = self.format_date(todo.due)
        summary = todo.summary

        return self.compact_format.format(completed=completed, urgent=urgent,
                                          due=due, summary=summary,
                                          percent=percent)

    def detailed(self, todo):
        """
        Returns a detailed representation of a task.

        :param Todo todo: The todo component.
        """
        done = "Done " if todo.percent_complete == 100 else ""
        urgent = "" if todo.priority in [None, 0] else "Urgent "
        if todo.due:
            due = "Due: {} ".format(self.format_date(todo.due))
        else:
            due = ""
        summary = todo.summary
        description = todo.description

        return self.detailed_format.format(done=done, urgent=urgent,
                                           due=due, summary=summary,
                                           description=description)

    def format_date(self, date):
        if date:
            return date.strftime(self.date_format)
        else:
            return self.empty_date

    def unformat_date(self, date):
        if date:
            date = datetime.strptime(date, self.date_format)
            return date.replace(tzinfo=self._localtimezone)
        else:
            return None
