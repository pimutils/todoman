import json
from datetime import datetime
from time import mktime

import click
import parsedatetime
import urwid
from dateutil.tz import tzlocal

from . import widgets

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

    def __init__(self, todo, databases, formatter):
        """
        :param model.Todo todo: The todo object which will be edited.
        """

        self.todo = todo
        self.databases = databases
        self.formatter = formatter
        self.saved = EditState.none
        self._loop = None

        self._msg_text = urwid.Text('')

        if todo.due:
            # TODO: use proper date_format
            due = formatter.format_date(todo.due)
        else:
            due = ""

        if todo.start:
            # TODO: use proper date_format
            dtstart = formatter.format_date(todo.start)
        else:
            dtstart = ''

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
        self._urgent = urwid.CheckBox("", state=todo.priority != 0)

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
                             ("Urgent", self._urgent),
                             ]:
            label = urwid.Text(label + ":", align='right')
            column = urwid.Columns([(13, label), field], dividechars=1)
            pile_items.append(('pack', column))

        grid = urwid.Pile(pile_items)
        spacer = urwid.Divider()

        self._ui_content = items = [grid, spacer, self._msg_text, buttons]
        self._ui = urwid.ListBox(items)

        self._help_text = urwid.Text(
            '\n\nGlobal:\n'
            ' F1: Toggle help\n'
            ' Ctrl-C: Cancel\n\n'
            'In Textfields:\n'
            + '\n'.join(' {}: {}'.format(k, v) for k, v
                        in widgets.ExtendedEdit.HELP)
        )

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

    def _save(self, btn):
        try:
            self._save_inner()
        except Exception as e:
            self.message(('error', str(e)))
        else:
            self.saved = EditState.saved
            raise urwid.ExitMainLoop()

    def _save_inner(self):
        self.todo.summary = self.summary
        self.todo.description = self.description
        self.todo.location = self.location
        if self.due:
            self.todo.due = self.formatter.unformat_date(self.due)
        else:
            self.todo.due = None

        if self.dtstart:
            self.todo.start = self.formatter.unformat_date(self.dtstart)
        else:
            self.todo.start = None

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

    def _cancel(self, btn):
        raise urwid.ExitMainLoop()

    def _keypress(self, key):
        if key.lower() == 'f1':
            self._toggle_help()

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


class TodoFormatter:

    # This one looks good with [X]
    compact_format = \
        "{id} [{completed}] {urgent} {due} {summary} {list}{percent}"
    # compact_format = "{completed} {urgent}  {due}  {summary}"

    def __init__(self, date_format, human_time):
        self.human_time = human_time
        self.date_format = date_format
        self._localtimezone = tzlocal()
        self.now = datetime.now().replace(tzinfo=self._localtimezone)
        self.empty_date = " " * len(self.format_date(self.now))

        if human_time:
            self._parsedatetime_calendar = parsedatetime.Calendar()

    def compact(self, todo, show_id=False):
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
            due = click.style(due, fg='red')

        summary = todo.summary
        list = self.format_database(todo.list)

        id_ = "{:3d}".format(todo.id) if show_id else ''

        return self.compact_format.format(
            completed=completed,
            due=due,
            id=id_,
            list=list,
            percent=percent,
            summary=summary,
            urgent=urgent,
        )

    def detailed(self, todo):
        """
        Returns a detailed representation of a task.

        :param Todo todo: The todo component.
        """
        rv = self.compact(todo)
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
        return '{}@{}'.format(database.color_ansi or '',
                              click.style(database.name))


class PorcelainFormatter:

    def compact(self, todo, show_id=None):
        data = dict(
            completed=todo.is_completed,
            due=self.format_date(todo.due),
            id=todo.id,
            list=todo.list.name,
            percent=todo.percent_complete,
            summary=todo.summary,
            # XXX: Move this into Todo itself and dedupe it
            urgent=todo.priority not in [None, 0],
        )

        return json.dumps(data, sort_keys=True)

    def format_date(self, date):
        if date:
            return int(date.timestamp())
        else:
            return None
