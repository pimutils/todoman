import json
from datetime import date
from datetime import datetime
from time import mktime
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import click
import humanize
import parsedatetime
import pytz
from dateutil.tz import tzlocal
from tabulate import tabulate

from todoman.model import Todo
from todoman.model import TodoList


def rgb_to_ansi(colour: Optional[str]) -> Optional[str]:
    """
    Convert a string containing an RGB colour to ANSI escapes
    """
    if not colour or not colour.startswith("#"):
        return None

    r, g, b = colour[1:3], colour[3:5], colour[5:7]

    if not len(r) == len(g) == len(b) == 2:
        return None

    return "\33[38;2;{!s};{!s};{!s}m".format(int(r, 16), int(g, 16), int(b, 16))


class DefaultFormatter:
    def __init__(
        self,
        date_format="%Y-%m-%d",
        time_format="%H:%M",
        dt_separator=" ",
        tz_override=None,
    ):
        self.date_format = date_format
        self.time_format = time_format
        self.dt_separator = dt_separator
        self.datetime_format = dt_separator.join(
            filter(bool, (date_format, time_format))
        )

        self.tz = tz_override or tzlocal()
        self.now = datetime.now().replace(tzinfo=self.tz)

        self._parsedatetime_calendar = parsedatetime.Calendar(
            version=parsedatetime.VERSION_CONTEXT_STYLE,
        )

    def simple_action(self, action: str, todo: Todo) -> str:
        return f'{action} "{todo.summary}"'

    def compact(self, todo: Todo) -> str:
        return self.compact_multiple([todo])

    def compact_multiple(self, todos: Iterable[Todo], hide_list=False) -> str:
        table = []
        for todo in todos:
            completed = "X" if todo.is_completed else " "
            percent = todo.percent_complete or ""
            if percent:
                percent = f" ({percent}%)"
            priority = self.format_priority_compact(todo.priority)

            due = self.format_datetime(todo.due)
            now = self.now if isinstance(todo.due, datetime) else self.now.date()
            if todo.due and todo.due <= now and not todo.is_completed:
                due = click.style(str(due), fg="red")

            recurring = "⟳" if todo.is_recurring else ""

            if hide_list:
                summary = "{} {}".format(
                    todo.summary,
                    percent,
                )
            else:
                if not todo.list:
                    raise ValueError("Cannot format todo without a list")

                summary = "{} {}{}".format(
                    todo.summary,
                    self.format_list(todo.list),
                    percent,
                )

            table.append(
                [
                    todo.id,
                    f"[{completed}]",
                    priority,
                    f"{due} {recurring}",
                    summary,
                ]
            )

        return tabulate(table, tablefmt="plain")

    def _columnize_text(
        self,
        label: str,
        text: Optional[str],
    ) -> List[Tuple[Optional[str], str]]:
        """Display text, split text by line-endings, on multiple colums.

        Do nothing if text is empty or None.
        """
        lines = text.splitlines() if text else None

        return self._columnize_list(label, lines)

    def _columnize_list(
        self,
        label: str,
        lst: Optional[List[str]],
    ) -> List[Tuple[Optional[str], str]]:
        """Display list on multiple columns.

        Do nothing if list is empty or None.
        """

        rows: List[Tuple[Optional[str], str]] = []

        if lst:
            rows.append((label, lst[0]))
            for line in lst[1:]:
                rows.append((None, line))

        return rows

    def detailed(self, todo: Todo) -> str:
        """Returns a detailed representation of a task.

        :param todo: The todo component.
        """
        extra_rows = []
        extra_rows += self._columnize_text("Description", todo.description)
        extra_rows += self._columnize_text("Location", todo.location)

        if extra_rows:
            return "{}\n\n{}".format(
                self.compact(todo), tabulate(extra_rows, tablefmt="plain")
            )
        return self.compact(todo)

    def format_datetime(self, dt: Optional[date]) -> Union[str, int, None]:
        if not dt:
            return ""
        elif isinstance(dt, datetime):
            return dt.strftime(self.datetime_format)
        elif isinstance(dt, date):
            return dt.strftime(self.date_format)

    def parse_priority(self, priority: Optional[str]) -> Optional[int]:
        if priority is None or priority == "":
            return None
        if priority == "low":
            return 9
        elif priority == "medium":
            return 5
        elif priority == "high":
            return 4
        elif priority == "none":
            return 0
        else:
            raise ValueError("Priority has to be one of low, medium, high or none")

    def format_priority(self, priority: Optional[int]) -> str:
        if not priority:
            return "none"
        elif 1 <= priority <= 4:
            return "high"
        elif priority == 5:
            return "medium"
        elif 6 <= priority <= 9:
            return "low"

    def format_priority_compact(self, priority: Optional[int]) -> str:
        if not priority:
            return ""
        elif 1 <= priority <= 4:
            return "!!!"
        elif priority == 5:
            return "!!"
        elif 6 <= priority <= 9:
            return "!"

    def parse_datetime(self, dt: str) -> Optional[date]:
        if not dt:
            return None

        rv = self._parse_datetime_naive(dt)
        return rv.replace(tzinfo=self.tz) if isinstance(rv, datetime) else rv

    def _parse_datetime_naive(self, dt: str) -> date:
        """Parse dt and returns a naive datetime or a date"""
        try:
            return datetime.strptime(dt, self.datetime_format)
        except ValueError:
            pass

        try:
            return datetime.strptime(dt, self.date_format).date()
        except ValueError:
            pass

        try:
            return datetime.combine(
                self.now.date(), datetime.strptime(dt, self.time_format).time()
            )
        except ValueError:
            pass

        rv, pd_ctx = self._parsedatetime_calendar.parse(dt)
        if not pd_ctx.hasDateOrTime:
            raise ValueError(f"Time description not recognized: {dt}")
        return datetime.fromtimestamp(mktime(rv))

    def format_list(self, database: TodoList):
        return "{}@{}".format(
            rgb_to_ansi(database.colour) or "", click.style(database.name)
        )

    def format_lists(self, lists) -> str:
        table = []
        for list_ in lists:
            table.append((list_.todo_count, self.format_list(list_)))

        return tabulate(table, tablefmt="plain")


class HumanizedFormatter(DefaultFormatter):
    def format_datetime(self, dt: Optional[date]) -> str:
        if not dt:
            return ""

        if isinstance(dt, datetime):
            rv = humanize.naturaltime(self.now - dt)
            if " from now" in rv:
                rv = "in {}".format(rv[:-9])
        elif isinstance(dt, date):
            rv = humanize.naturaldate(dt)

        return rv


class PorcelainFormatter(DefaultFormatter):
    def _todo_as_dict(self, todo):
        return {
            "completed": todo.is_completed,
            "due": self.format_datetime(todo.due),
            "id": todo.id,
            "list": todo.list.name,
            "percent": todo.percent_complete,
            "summary": todo.summary,
            "priority": todo.priority,
            "location": todo.location,
            "description": todo.description,
            "completed_at": self.format_datetime(todo.completed_at),
        }

    def compact(self, todo: Todo) -> str:
        return json.dumps(self._todo_as_dict(todo), indent=4, sort_keys=True)

    def compact_multiple(self, todos: Iterable[Todo], hide_list=False) -> str:
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
                raise ValueError("Priority has to be in the range 0-9")
        except ValueError as e:
            raise click.BadParameter(e)

    def detailed(self, todo):
        return self.compact(todo)

    def format_datetime(self, value: Optional[date]) -> Optional[int]:
        if value:
            if not isinstance(value, datetime):
                dt = datetime.fromordinal(value.toordinal())
            else:
                dt = value
            return int(dt.timestamp())
        else:
            return None

    def parse_datetime(self, value):
        if value:
            return datetime.fromtimestamp(value, tz=pytz.UTC)
        else:
            return None

    def format_lists(self, lists: Iterable[TodoList]) -> str:
        return json.dumps(
            [
                {
                    "color": list_.colour,
                    "name": list_.name,
                    "todo_count": list_.todo_count,
                }
                for list_ in lists
            ],
            indent=2,
        )
