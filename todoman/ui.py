import datetime
import json
from time import mktime

import click
import humanize
import parsedatetime
import urwid
from dateutil.tz import tzlocal
from tabulate import tabulate


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
        self._categories = widgets.ExtendedEdit(
            parent=self,
            edit_text=','.join(todo.categories)
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
                             ("Categories", self._categories),
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
        self._ui = urwid.ListBox(items)

        self._help_text = urwid.Text(
            '\n\nGlobal:\n'
            ' F1: Toggle help\n'
            ' Ctrl-C: Cancel\n'
            ' Ctrl-S: Save (only works if not a shell shortcut already)\n\n'
            'In Textfields:\n'
            + '\n'.join(' {}: {}'.format(k, v) for k, v
                        in widgets.ExtendedEdit.HELP)
        )

        def change_current_list(radio_button, new_state, new_list):
            if new_state:
                self.current_list = new_list

        list_selector = []
        for _list in self.lists:
            urwid.RadioButton(list_selector, _list.name,
                              state=_list.name == self.current_list.name,
                              on_state_change=change_current_list,
                              user_data=_list)
        items.append(urwid.Pile(list_selector))

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
        self.todo.raw_categories = self.categories
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
    def categories(self):
        return self._categories.edit_text

    @property
    def due(self):
        return self._due.edit_text

    @property
    def dtstart(self):
        return self._dtstart.edit_text

    @property
    def priority(self):
        return self._priority.edit_text


class DefaultFormatter:

    def __init__(self, date_format, time_format, dt_separator):
        self.date_format = date_format
        self.time_format = time_format
        self.dt_separator = dt_separator
        self.datetime_format = dt_separator.join(filter(bool, (
            date_format, time_format
        )))

        self._localtimezone = tzlocal()
        self.now = datetime.datetime.now().replace(tzinfo=self._localtimezone)

        self._parsedatetime_calendar = parsedatetime.Calendar()

    def simple_action(self, action, todo):
        return '{} "{}"'.format(action, todo.summary)

    def compact(self, todo):
        return self.compact_multiple([todo])

    def compact_multiple(self, todos):
        table = []
        for todo in todos:
            completed = "X" if todo.is_completed else " "
            percent = todo.percent_complete or ''
            if percent:
                percent = " ({}%)".format(percent)
            priority = self.format_priority_compact(todo.priority)

            due = self.format_datetime(todo.due)
            if todo.due and todo.due <= self.now and not todo.is_completed:
                due = click.style(due, fg='red')

            table.append([
                todo.id,
                "[{}]".format(completed),
                priority,
                due,
                "{} {}{}".format(
                    todo.summary,
                    self.format_database(todo.list),
                    percent,
                ),
            ])

        return tabulate(table, tablefmt='plain')

    def detailed(self, todo):
        """
        Returns a detailed representation of a task.

        :param Todo todo: The todo component.
        """
        rv = self.compact_multiple([todo])
        if todo.description:
            rv = "{}\n\nDescription : {}".format(rv, todo.description)
        if todo.categories:
            rv = "{}\n\nCategories : {}".format(rv, todo.categories)
        if todo.location:
            rv = "{}\n\nLocation: {}".format(rv, todo.location)
        return rv

    def format_datetime(self, dt):
        if not dt:
            return ''
        elif isinstance(dt, datetime.datetime):
            return dt.strftime(self.datetime_format)
        elif isinstance(dt, datetime.date):
            return dt.strftime(self.date_format)

    def parse_category(self, categories):
        if not categories:
            return None
        if ',' in categories:
            return categories.split(',')
        else:
            return [categories]

    def parse_priority(self, priority):
        if priority is None or priority is '':
            return None
        if priority == 'low':
            return 9
        elif priority == 'medium':
            return 5
        elif priority == 'high':
            return 4
        elif priority == 'none':
            return 0
        else:
            raise ValueError('Priority has to be one of low, medium,'
                             ' high or none')

    def format_priority(self, priority):
        if not priority:
            return ''
        elif 1 <= priority <= 4:
            return 'high'
        elif priority == 5:
            return 'medium'
        elif 6 <= priority <= 9:
            return 'low'

    def format_priority_compact(self, priority):
        if not priority:
            return ''
        elif 1 <= priority <= 4:
            return "!!!"
        elif priority == 5:
            return "!!"
        elif 6 <= priority <= 9:
            return "!"

    def parse_datetime(self, dt):
        if not dt:
            return None

        rv = self._parse_datetime_naive(dt)
        return rv.replace(tzinfo=self._localtimezone)

    def _parse_datetime_naive(self, dt):
        try:
            return datetime.datetime.strptime(dt, self.datetime_format)
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(dt, self.date_format)
        except ValueError:
            pass

        try:
            return datetime.datetime.combine(
                self.now.date(),
                datetime.datetime.strptime(dt, self.time_format).time()
            )
        except ValueError:
            pass

        rv, certainty = self._parsedatetime_calendar.parse(dt)
        if not certainty:
            raise ValueError(
                'Time description not recognized: {}' .format(dt)
            )
        return datetime.datetime.fromtimestamp(mktime(rv))

    def format_database(self, database):
        return '{}@{}'.format(database.color_ansi or '',
                              click.style(database.name))


class HumanizedFormatter(DefaultFormatter):

    def format_datetime(self, dt):
        if not dt:
            return ''
        return humanize.naturaltime(self.now - dt)


class PorcelainFormatter(DefaultFormatter):

    def __init__(self, *args, **kwargs):
        pass

    def _todo_as_dict(self, todo):
        return dict(
            completed=todo.is_completed,
            due=self.format_datetime(todo.due),
            id=todo.id,
            list=todo.list.name,
            percent=todo.percent_complete,
            summary=todo.summary,
            priority=todo.priority,
        )

    def compact(self, todo):
        return json.dumps(self._todo_as_dict(todo), indent=4, sort_keys=True)

    def compact_multiple(self, todos):
        data = [self._todo_as_dict(todo) for todo in todos]
        return json.dumps(data, indent=4, sort_keys=True)

    def simple_action(self, action, todo):
        return self.compact(todo)

    def parse_priority(self, priority):
        if priority is None:
            return None
        try:
            if int(priority) in range(0, 10):
                return int(priority)
            else:
                raise ValueError('Priority has to be in the range 0-9')
        except ValueError as e:
            raise click.BadParameter(e)

    def detailed(self, todo):
        return self.compact(todo)

    def format_datetime(self, date):
        if date:
            return int(date.timestamp())
        else:
            return None

    def parse_datetime(self, value):
        if value:
            return datetime.datetime.fromtimestamp(value)
        else:
            return None
