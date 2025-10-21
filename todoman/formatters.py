from __future__ import annotations

import contextlib
import json
from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from datetime import tzinfo
from time import mktime

import click
import humanize
import parsedatetime
from dateutil.tz import tzlocal

from todoman.model import Todo
from todoman.model import TodoList

def rgb_to_ansi(colour: str | None) -> str | None:
    """
    Convert a string containing an RGB colour to ANSI escapes
    """
    if not colour or not colour.startswith("#"):
        return None

    r, g, b = colour[1:3], colour[3:5], colour[5:7]

    if not len(r) == len(g) == len(b) == 2:
        return None

    return f"\33[38;2;{int(r, 16)!s};{int(g, 16)!s};{int(b, 16)!s}m"


class Formatter(ABC):
    @abstractmethod
    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        time_format: str = "%H:%M",
        dt_separator: str = " ",
    ) -> None:
        """Create a new formatter instance."""

    @abstractmethod
    def compact(self, todo: Todo) -> str:
        """Render a compact todo (usually in a single line)"""

    @abstractmethod
    def compact_multiple(self, todos: Iterable[Todo], hide_list: bool = False) -> str:
        """Same as compact() but for multiple todos."""

    @abstractmethod
    def simple_action(self, action: str, todo: Todo) -> str:
        """Render an action related to a todo (e.g.: compelete, undo, etc)."""

    @abstractmethod
    def parse_priority(self, priority: str | None) -> int | None:
        """Parse a priority"""

    @abstractmethod
    def detailed(self, todo: Todo) -> str:
        """Returns a detailed representation of a task."""

    @abstractmethod
    def format_datetime(self, value: date | None) -> str | int | None:
        """Format an optional datetime."""

    @abstractmethod
    def parse_datetime(self, value: str | None) -> date | None:
        """Parse an optional datetime."""

    @abstractmethod
    def format_database(self, database: TodoList) -> str:
        """Format the name of a single database."""

    @abstractmethod
    def parse_categories(self, categories: str) -> list[str]:
        """Parse multiple categories."""

    @abstractmethod
    def format_categories(self, categories: Iterable[str]) -> str:
        """Format multiple categories."""

    @abstractmethod
    def format_priority(self, priority: int | None) -> str:
        """Format a todo priority"""


class DefaultFormatter(Formatter):
    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        time_format: str = "%H:%M",
        dt_separator: str = " ",
        tz_override: tzinfo | None = None,
    ) -> None:
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

    def compact_multiple(self, todos: Iterable[Todo],
                         hide_list: bool = False) -> str:
        # TODO: show dates that are in the future in yellow (in 24hs)
        # or grey (future)

        # Holds information needed to properly order the text output.
        #
        # key: UID of todo
        # value: list which contains 2 elements:
        #            0: the formatted todo text line for the output
        #            1: a dictionary which represents child todos which have
        #               the same structure as the parent
        tree: dict[str, list] = {}

        # Holds all of the todo relationships in the form of key-value pairs.
        #
        # key: child
        # value: list which contains 2 elements:
        #            0: parent
        #            1: any special information like "SIBLING"
        related_todos: dict[str, list] = {}

        for todo in todos:
            # If RELTYPE is empty, the default is PARENT.
            # Source:
            # https://www.rfc-editor.org/rfc/rfc5545#section-3.2.15
            #
            # "To preserve backwards compatibility, the value type MUST be
            # UID when the PARENT, SIBLING, or CHILD relationships
            # are specified."
            # Source:
            # https://www.rfc-editor.org/rfc/rfc9253#section-9.1
            if todo.related_to != "":
                if todo.related_to_reltype == "PARENT" \
                        or todo.related_to_reltype == "":
                    related_todos[todo.uid] = [todo.related_to, None]
                elif todo.related_to_reltype == "CHILD":
                    related_todos[todo.related_to] = [todo.uid, None]
                elif todo.related_to_reltype == "SIBLING":
                    related_todos[todo.uid] = [todo.related_to, "SIBLING"]

            completed = "X" if todo.is_completed else " "

            percent = todo.percent_complete or ""
            if percent:
                percent = f" ({percent}%)"

            if todo.categories:
                categories = "[" + ", ".join(todo.categories) + "]"
            else:
                categories = ""

            priority = self.format_priority_compact(todo.priority)
            if priority != "":
                priority = click.style(priority + " ", fg="magenta",)

            due = self.format_datetime(todo.due) or "(no due date)"
            due_colour = self._due_colour(todo)
            if due_colour:
                due = click.style(str(due), fg=due_colour)

            recurring = "⟳ " if todo.is_recurring else ""

            if hide_list:
                summary = f"{todo.summary}{percent}"
            else:
                if not todo.list:
                    raise ValueError("Cannot format todo without a list")

                summary = f"{todo.summary} "\
                          f"{self.format_database(todo.list)}{percent}"

            tree[todo.uid] = [f"[{completed}] {todo.id} {priority}{due} "
                              f"{recurring}{summary} {categories}\n",
                              None]

        self._tree_reorder_related(tree, related_todos)

        return self._join_tree(tree).strip()

    def _tree_reorder_related(self, tree: dict[str, list],
                              related_todos: dict[str, list]) -> None:
        """Move all related todos to their proper positions within the tree
        dictionary."""
        store_path: list = []
        for related, related_to in related_todos.items():
            # Find the root parent todo of the `related_to` todo.
            related_to_path_tracer: str = related_to[0]
            related_dict: dict[str, list] = tree
            while related_to_path_tracer in related_todos:
                related_to_path_tracer = \
                        related_todos[related_to_path_tracer][0]
                store_path.append(related_to_path_tracer)

            # Walk from the parent root todo, down to the
            # `related_to` todo itself.
            store_path.reverse()
            # If `related_to` is a SIBLING, walk one todo backwards towards the
            # root parent todo. If there is no path to be walked,
            # just ignore it.
            with contextlib.suppress(IndexError):
                if related_to[1] == "SIBLING":
                    related_to[0] = store_path.pop()
            for inwards in store_path:
                try:
                    related_dict = related_dict[inwards][1]
                    if related_dict is None:
                        break
                except KeyError:
                    related_dict = tree
                    break

            self._tree_move_related(related, related_to[0],
                                    tree, related_dict)

            store_path.clear()

    def _tree_move_related(self, related: str, to: str,
                           tree: dict[str, list],
                           related_dict: dict[str, list] | None) -> None:
        """Move a todo from the top of the tree dictionary, to the child
        dictionary of a todo."""
        if related_dict is None:
            related_dict = tree

        if related not in tree or to not in related_dict:
            return

        if related_dict[to][1] is None:
            related_dict[to][1] = {related: tree.pop(related)}
        else:
            related_dict[to][1][related] = tree.pop(related)

    def _join_tree(self, tree: dict[str, list], space: str = "") -> str:
        """Recursively walk the whole tree dictionary and combine all todos as
        an indented text output."""
        output: str = ""
        prev_space: str = space
        for _, val in tree.items():
            output = output + space + val[0]
            if val[1] is not None:
                space = space + "    "
                output = output + self._join_tree(val[1], space)
            space = prev_space
        return output

    def _due_colour(self, todo: Todo) -> str:
        now = self.now if isinstance(todo.due, datetime) else self.now.date()
        if todo.due:
            if todo.due <= now and not todo.is_completed:
                return "red"
            if todo.due >= now + timedelta(hours=24):
                return "white"
            if todo.due >= now:
                return "yellow"

        return "white"

    def _format_multiline(self, title: str, value: str) -> str:
        formatted_title = click.style(title, fg="white")

        if value.strip().count("\n") == 0:
            return f"\n\n{formatted_title}: {value}"
        return f"\n\n{formatted_title}:\n{value}"

    def detailed(self, todo: Todo) -> str:
        extra_lines = []
        if todo.description:
            extra_lines.append(self._format_multiline("Description", todo.description))

        if todo.location:
            extra_lines.append(self._format_multiline("Location", todo.location))

        return f"{self.compact(todo)}{''.join(extra_lines)}"

    # FIXME: cannot return `int`, but porcelain subclasses this (it shouldn't)
    def format_datetime(self, dt: date | None) -> str | int | None:
        if not dt:
            return ""
        if isinstance(dt, datetime):
            return dt.strftime(self.datetime_format)
        if isinstance(dt, date):
            return dt.strftime(self.date_format)
        return None

    def format_categories(self, categories: Iterable[str]) -> str:
        return ", ".join(categories)

    def parse_categories(self, categories: str) -> list[str]:
        # existing code assumes categories is list,
        # but click passes tuple
        return list(categories)

    def parse_priority(self, priority: str | None) -> int | None:
        if priority is None or priority == "":
            return None
        if priority == "low":
            return 9
        if priority == "medium":
            return 5
        if priority == "high":
            return 4
        if priority == "none":
            return 0
        raise ValueError("Priority has to be one of low, medium, high or none")

    def format_priority(self, priority: int | None) -> str:
        if not priority:
            return "none"
        if 1 <= priority <= 4:
            return "high"
        if priority == 5:
            return "medium"
        if 6 <= priority <= 9:
            return "low"

        raise ValueError("priority is an invalid value")

    def format_priority_compact(self, priority: int | None) -> str:
        if not priority:
            return ""
        if 1 <= priority <= 4:
            return "!!!"
        if priority == 5:
            return "!!"
        if 6 <= priority <= 9:
            return "!"

        raise ValueError("priority is an invalid value")

    def parse_datetime(self, dt: str | None) -> date | None:
        if not dt:
            return None

        rv = self._parse_datetime_naive(dt)
        return rv.replace(tzinfo=self.tz) if isinstance(rv, datetime) else rv

    def _parse_datetime_naive(self, dt: str) -> date:
        """Parse dt and returns a naive datetime or a date"""
        with contextlib.suppress(ValueError):
            return datetime.strptime(dt, self.datetime_format)

        with contextlib.suppress(ValueError):
            return datetime.strptime(dt, self.date_format).date()

        with contextlib.suppress(ValueError):
            return datetime.combine(
                self.now.date(), datetime.strptime(dt, self.time_format).time()
            )

        rv, pd_ctx = self._parsedatetime_calendar.parse(dt)
        if not pd_ctx.hasDateOrTime:
            raise ValueError(f"Time description not recognized: {dt}")
        return datetime.fromtimestamp(mktime(rv))

    def format_database(self, database: TodoList) -> str:
        return "{}@{}".format(
            rgb_to_ansi(database.colour) or "", click.style(database.name)
        )


class HumanizedFormatter(DefaultFormatter):
    def format_datetime(self, dt: date | None) -> str:
        if not dt:
            return ""

        if isinstance(dt, datetime):
            rv = humanize.naturaltime(self.now - dt)
            if " from now" in rv:
                rv = f"in {rv[:-9]}"
        elif isinstance(dt, date):
            rv = humanize.naturaldate(dt)

        return rv


class PorcelainFormatter(DefaultFormatter):
    def _todo_as_dict(self, todo: Todo) -> dict:
        return {
            "completed": todo.is_completed,
            "start": self.format_datetime(todo.start),
            "due": self.format_datetime(todo.due),
            "id": todo.id,
            "list": todo.list.name if todo.list else None,
            "list_colour": todo.list.colour if todo.list else None,
            "percent": todo.percent_complete,
            "summary": todo.summary,
            "categories": todo.categories,
            "priority": todo.priority,
            "location": todo.location,
            "description": todo.description,
            "completed_at": self.format_datetime(todo.completed_at),
            "recurring": todo.is_recurring,
            "related_to": todo.related_to,
            "related_to_reltype": todo.related_to_reltype,
        }

    def compact(self, todo: Todo) -> str:
        return json.dumps(self._todo_as_dict(todo), indent=4, sort_keys=True)

    def compact_multiple(self, todos: Iterable[Todo], hide_list: bool = False) -> str:
        data = [self._todo_as_dict(todo) for todo in todos]
        return json.dumps(data, indent=4, sort_keys=True)

    def simple_action(self, action: str, todo: Todo) -> str:
        return self.compact(todo)

    def parse_priority(self, priority: str | None) -> int | None:
        if priority is None:
            return None
        try:
            if int(priority) in range(10):
                return int(priority)
            raise ValueError("Priority has to be in the range 0-9")
        except ValueError as e:
            raise click.BadParameter(str(e)) from None

    def detailed(self, todo: Todo) -> str:
        return self.compact(todo)

    def format_datetime(self, value: date | None) -> int | None:
        if value:
            if not isinstance(value, datetime):
                dt = datetime.fromordinal(value.toordinal())
            else:
                dt = value
            return int(dt.timestamp())
        return None

    def parse_datetime(self, value: str | float | None) -> datetime | None:
        if value:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        return None
