import icalendar
import logging
import os
from uuid import uuid4
from datetime import datetime, timedelta

logger = logging.getLogger(name=__name__)
# logger.addHandler(logging.FileHandler('model.log'))


class Todo:
    """
    Represents a task/todo, and wrapps around icalendar.Todo.

    All text attributes are always treated as text, and "" will be returned if
    they are not defined.
    Date attributes are treated as datetime objects, and None will be returned
    if they are not defined.
    """

    def __init__(self, todo=None, filename=None):
        """
        :param icalendar.Todo todo: The icalendar component object on which
        this todo is based. If None is passed, a new one is created.
        :param str filename: The name of the file for this todo. Defaults to
        the <uid>.ics
        """

        if todo:
            self.todo = todo
        else:
            self.todo = icalendar.Todo()
            self.todo.add('uid', uuid4())
            self.todo.add('due', datetime.today() + timedelta(days=1))
            self.todo.add('percent-complete', 0)
            self.todo.add('priority', 0)
            self.todo.add('created', datetime.now())

        if filename:
            self.filename = filename
        else:
            self.filename = "{}.ics".format(self.todo.get('uid'))

    def _set_field(self, name, value, force=False):
        if name in self.todo:
            del(self.todo[name])
        if value or force:
            logger.debug("Setting field %s to %s.", name, value)
            self.todo.add(name, value)

    def get_summary(self):
        return self.todo.get('summary', "")

    def set_summary(self, summary):
        self._set_field('summary', summary)

    def get_description(self):
        return self.todo.get('description', "")

    def set_description(self, description):
        self._set_field('description', description)

    def get_location(self):
        return self.todo.get('location', "")

    def set_location(self, location):
        self._set_field('location', location)

    def get_due(self):
        """
        Returns the due date, as a datetime object, if set, or None.
        """
        if self.todo.get('due', None) is None:
            return None
        else:
            return self.todo.decoded('due')

    def set_due(self, due):
        self._set_field('due', due)

    def get_completed(self):
        return self.todo.get('completed', None)

    def set_completed(self, completed):
        self._set_field('completed', completed)

    def get_percent_complete(self):
        return int(self.todo.get('percent-complete', 0))

    def set_percent_complete(self, percent_complete):
        self._set_field('percent-complete', percent_complete, force=True)

    def get_priority(self):
        return self.todo.get('priority', None)

    def set_priority(self, priority):
        self._set_field('priority', priority, force=True)

    summary = property(get_summary, set_summary)
    description = property(get_description, set_description)
    location = property(get_location, set_location)
    due = property(get_due, set_due)
    completed = property(get_completed, set_completed)
    percent_complete = property(get_percent_complete, set_percent_complete)
    priority = property(get_priority, set_priority)

    @property
    def uid(self):
        return self.todo.get('uid')

    def to_ical(self):
        return self.todo.to_ical()


class Database:
    """
    This class is essentially a wrapper around the a directory which contains a
    bunch of ical files. While not a traditional SQL database, it's still *our*
    database.
    """

    def __init__(self, path):
        self.path = path

    def _read(self):
        self.todos = []
        for entry in [f for f in os.listdir(self.path) if f.endswith(".ics")]:
            with open(os.path.join(self.path, entry), 'rb') as f:
                try:
                    cal = icalendar.Calendar.from_ical(f.read())
                    for component in cal.walk('VTODO'):
                        todo = Todo(component, entry)
                        self.todos.append(todo)
                except Exception as e:
                    logger.warn("Failed to read entry %s: %s.", entry, e)
        self.todos.sort(key=self._sort_func)

    def set_path(self, path):
        self._path = path
        self._read()

    def get_path(self):
        return self._path

    path = property(get_path, set_path)

    @staticmethod
    def _sort_func(todo):
        """ Auxiliary function used to sort todos.  """

        # Timestamps are strings, so this uses string comparison, so appending
        # infront doesn't have the effect you'd expect when doing that with
        # integers.

        if todo.due and todo.priority not in [None, 0]:
            return "0" + todo.due.strftime("%s")
        elif todo.priority not in [None, 0]:
            return "3"
        elif todo.due:
            return "6" + todo.due.strftime("%s")
        else:
            return "9"

    def get_nth(self, n):
        if n < len(self.todos) + 1:
            return self.todos[n - 1]
        return None

    def save(self, todo):
        path = os.path.join(self.path, todo.filename)

        if os.path.exists(path):
            # Update an existing entry:
            with open(path, 'rb') as f:
                cal = icalendar.Calendar.from_ical(f.read())
                for index, component in enumerate(cal.subcomponents):
                    if component.get('uid', None) == todo.uid:
                        cal.subcomponents[index] = todo.todo

            with open(path, 'wb') as f:
                f.write(cal.to_ical())
        else:
            # Save a new entry:
            c = icalendar.Calendar()
            c.add('prodid', 'io.barrera.todoman')
            c.add('version', '2.0')
            c.add_component(todo.todo)

            with open(path, 'wb') as f:
                f.write(c.to_ical())
