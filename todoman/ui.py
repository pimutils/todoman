from datetime import datetime
from time import mktime

import parsedatetime
import urwid
import ansi.colour.fx
import ansi.colour.fg
import ansi.sequence
from dateutil.tz import tzlocal


class TodoEditor:
    """
    The UI for a single todo entry.
    """

    def __init__(self, todo, databases, formatter):
        """
        :param model.Todo todo: The todo object which will be edited.
        """

        self.todo = todo
        self.databases = databases
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
        self._completed = urwid.CheckBox("", state=todo.is_completed)
        self._urgent = urwid.CheckBox("", state=todo.priority != 0)

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
        loop = urwid.MainLoop(self._ui, unhandled_input=self._keypress,
                              handle_mouse=False)
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

        self.todo.is_completed = self._completed.get_state()

        # If it was already non-zero, keep it that way. Let's not overwrite
        # values 1 thru 8.
        if self._urgent.get_state() and not self.todo.priority:
            self.todo.priority = 9
        elif not self._urgent.get_state():
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
    compact_format = \
        "[{completed}] {urgent} {due} {summary} {list}{percent}"
    # compact_format = "{completed} {urgent}  {due}  {summary}"

    def __init__(self, date_format, human_time):
        self.human_time = human_time
        self.date_format = date_format
        self._localtimezone = tzlocal()
        self.now = datetime.now().replace(tzinfo=self._localtimezone)
        self.empty_date = " " * len(self.format_date(self.now))

        if human_time:
            self._parsedatetime_calendar = parsedatetime.Calendar()

    def compact(self, todo, database):
        """
        Returns a brief representation of a task, suitable for displaying
        on-per-line.

        :param Todo todo: The todo component.
        """
        # completed = "✓" if todo.percent_complete == 100 else " "
        completed = "X" if todo.is_completed else " "
        percent = todo.percent_complete or ''
        if percent:
            percent = " ({}%)".format(percent)
        urgent = " " if todo.priority in [None, 0] else "!"

        due = self.format_date(todo.due)
        if todo.due and todo.due <= self.now and not todo.is_completed:
            due = '{}{}{}'.format(
                ansi.colour.fg.red,
                due,
                ansi.colour.fx.reset
            )

        summary = todo.summary
        list = self.format_database(database)

        return self.compact_format.format(completed=completed, urgent=urgent,
                                          due=due, summary=summary, list=list,
                                          percent=percent)

    def detailed(self, todo, database):
        """
        Returns a detailed representation of a task.

        :param Todo todo: The todo component.
        """
        rv = self.compact(todo, database)
        if todo.description:
            rv = "{}\n\n{}".format(rv, todo.description)
        return rv

    def format_date(self, date):
        if date:
            rv = date.strftime(self.date_format)
            return rv
        else:
            return self.empty_date

    def unformat_date(self, date):
        if date:
            try:
                rv = datetime.strptime(date, self.date_format)
            except ValueError:
                if not self.human_time:
                    raise

                rv, certainty = self._parsedatetime_calendar.parse(date)
                if not certainty:
                    raise ValueError('Time description not recognized: {}'
                                     .format(date))
                rv = datetime.fromtimestamp(mktime(rv))

            return rv.replace(tzinfo=self._localtimezone)

        else:
            return None

    def format_database(self, database):
        return '{}@{}{}'.format(database.color_ansi or '',
                                database.name,
                                ansi.colour.fx.reset)
