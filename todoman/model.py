import logging
import os
from uuid import uuid4
from datetime import datetime, timedelta

import icalendar
from atomicwrites import AtomicWriter

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

    @property
    def summary(self):
        return self.todo.get('summary', "")

    @summary.setter
    def summary(self, summary):
        self._set_field('summary', summary)

    @property
    def description(self):
        return self.todo.get('description', "")

    @description.setter
    def description(self, description):
        self._set_field('description', description)

    @property
    def location(self):
        return self.todo.get('location', "")

    @location.setter
    def location(self, location):
        self._set_field('location', location)

    @property
    def due(self):
        """
        Returns the due date, as a datetime object, if set, or None.
        """
        if self.todo.get('due', None) is None:
            return None
        else:
            return self.todo.decoded('due')

    @due.setter
    def due(self, due):
        self._set_field('due', due)

    @property
    def completed(self):
        if self.todo.get('completed', None) is None:
            return None
        else:
            return self.todo.decoded('completed')

    @completed.setter
    def completed(self, completed):
        self._set_field('completed', completed)

    @property
    def percent_complete(self):
        return int(self.todo.get('percent-complete', 0))

    @percent_complete.setter
    def percent_complete(self, percent_complete):
        self._set_field('percent-complete', percent_complete, force=True)

    @property
    def priority(self):
        return self.todo.get('priority', None)

    @priority.setter
    def priority(self, priority):
        self._set_field('priority', priority, force=True)

    @property
    def uid(self):
        return self.todo.get('uid')

    def complete(self):
        self.completed = datetime.now()
        self.percent_complete = 100

    def undo(self):
        for name in ['completed', 'percent-complete']:
            if name in self.todo:
                del(self.todo[name])


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

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path
        self._read()

    @staticmethod
    def _sort_func(todo):
        """
        Auxiliary function used to sort todos.

        We put the most important items on the bottom of the list because the
        terminal scrolls with the output.
        """

        rv = (todo.priority or 0),
        if todo.due:
            rv += (todo.due,)
        return rv

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

            with AtomicWriter(path, overwrite=True).open() as f:
                f.write(cal.to_ical().decode("UTF-8"))
        else:
            # Save a new entry:
            c = icalendar.Calendar()
            c.add('prodid', 'io.barrera.todoman')
            c.add('version', '2.0')
            c.add_component(todo.todo)

            with AtomicWriter(path).open() as f:
                f.write(cal.to_ical().decode("UTF-8"))
