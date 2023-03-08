import json

from datetime import timedelta
from typing import Dict, List

from todoman.model import Todo
from todoman import exceptions


class DefaultParser:
    """ """

    def __init__(
        self,
        date_format="%Y-%m-%d",
        time_format="%H:%M",
        dt_separator=" ",
        list_: str = None,
        new: bool = False,
        ctx=None,
    ):
        self.list_ = list_
        self.new = new
        self.ctx = ctx

    def parse(self, data: Dict, new: bool = None) -> List[Todo]:
        """
        Read DATA and parse into one or more Todos.

        The DefaultParser only handles values for a single Todo from the
        command line.
        """
        todo = Todo(new=True, list=self.list_)

        default_due = self.ctx.config["default_due"]
        if default_due:
            todo.due = todo.created_at + timedelta(hours=default_due)

        default_priority = self.ctx.config["default_priority"]
        if default_priority is not None:
            todo.priority = default_priority

        for key, value in data.items():
            if value is not None:
                setattr(todo, key, value)

        return [todo]


class JsonParser(DefaultParser):
    SETTABLE_KEYS = [
        "completed_at",
        "description",
        "due",
        "location",
        "percent",
        "priority",
        "start",
        "summary",
    ]

    def _parse_todo_properties(self, todo: Todo, properties: Dict) -> Dict:
        for key, value in properties.items():
            if key in JsonParser.SETTABLE_KEYS and value:
                setattr(todo, key, value)

    def _parse_todos(self, *todo_dicts: Dict) -> List[Todo]:
        todos = []
        for todo_raw in todo_dicts:
            if self.new:
                todo = Todo(new=True, list=self.list_)
            else:
                todo = Todo(new=False, list=self.list_)
                try:
                    todo.id = todo_raw["id"]
                except KeyError:
                    raise exceptions.FormatError(todo_raw.get("id"), "integer", "id")
            self._parse_todo_properties(todo, todo_raw)
            todos.append(todo)

        return todos

    def parse(self, json_str: str) -> List[Todo]:
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as err:
            # TODO(skowalak): handle err
            raise exceptions.FormatError(json_str, "json", "stdin")

        if isinstance(json_data, list):
            # more than one todo read
            return self._parse_todos(*json_data)
        elif isinstance(json_data, dict):
            return self._parse_todos(json_data)
