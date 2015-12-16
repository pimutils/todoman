import logging
import os
from os.path import split, normpath
from uuid import uuid4
from datetime import date, time, datetime, timedelta

import icalendar
from ansi.colour.rgb import rgb8
from atomicwrites import AtomicWriter
from dateutil.tz import tzlocal

logger = logging.getLogger(name=__name__)
# logger.addHandler(logging.FileHandler('model.log'))


class cached_property:
    '''A read-only @property that is only evaluated once. Only usable on class
    instances' methods.
    '''
    def __init__(self, fget, doc=None):
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        self.__doc__ = doc or fget.__doc__
        self.fget = fget

    def __get__(self, obj, cls):
        if obj is None:  # pragma: no cover
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


class Todo:
    """
    Represents a task/todo, and wrapps around icalendar.Todo.

    All text attributes are always treated as text, and "" will be returned if
    they are not defined.
    Date attributes are treated as datetime objects, and None will be returned
    if they are not defined.
    All datetime objects have tzinfo, either the one defined in the file, or
    the local system's one.
    """

    _localtimezone = tzlocal()

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
            now = datetime.now(self._localtimezone)
            self.todo = icalendar.Todo()
            self.todo.add('uid', uuid4())
            self.todo.add('due', now + timedelta(days=1))
            self.todo.add('percent-complete', 0)
            self.todo.add('priority', 0)
            self.todo.add('created', now)

        self.filename = filename or "{}.ics".format(self.todo.get('uid'))

    def _set_field(self, name, value, force=False):
        if name in self.todo:
            del(self.todo[name])
        # XXX: Do I really want this check? What good does it do?
        if value or force:
            logger.debug("Setting field %s to %s.", name, value)
            self.todo.add(name, value)

    @property
    def status(self):
        return self.todo.get('status', 'NEEDS-ACTION')

    @status.setter
    def status(self, value):
        self._set_field('status', value)

    @property
    def is_completed(self):
        return bool(self.completed_at) or \
            self.status in ('CANCELLED', 'COMPLETED')

    @is_completed.setter
    def is_completed(self, val):
        if val:
            # Don't fiddle with completed_at if this was already completed:
            if not self.is_completed:
                self.completed_at = self._normalize_datetime(datetime.now())
            self.percent_complete = 100
            self.status = 'COMPLETED'
        else:
            for name in ['completed', 'percent-complete']:
                if name in self.todo:
                    del(self.todo[name])
            self.status = 'NEEDS-ACTION'

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
            return self._normalize_datetime(self.todo.decoded('due'))

    @due.setter
    def due(self, due):
        self._set_field('due', due)

    @property
    def completed_at(self):
        if self.todo.get('completed', None) is None:
            return None
        else:
            return self._normalize_datetime(self.todo.decoded('completed'))

    @completed_at.setter
    def completed_at(self, completed):
        self._set_field('completed', completed)

    @property
    def percent_complete(self):
        return int(self.todo.get('percent-complete', 0))

    @percent_complete.setter
    def percent_complete(self, percent_complete):
        self._set_field('percent-complete', percent_complete, force=True)

    @property
    def priority(self):
        return self.todo.get('priority', 0)

    @priority.setter
    def priority(self, priority):
        self._set_field('priority', priority, force=True)

    @property
    def created_at(self):
        if self.todo.get('created', None) is None:
            return None
        else:
            return self._normalize_datetime(self.todo.decoded('created'))

    @created_at.setter
    def created_at(self, created):
        self._set_field('created', created)

    @property
    def uid(self):
        return self.todo.get('uid')

    def _normalize_datetime(self, x):
        '''
        Eliminate several differences between dates, times and datetimes which
        are hindering comparison:

        - Convert everything to datetime
        - Add missing timezones
        '''
        if isinstance(x, date):
            x = datetime(x.year, x.month, x.day)
        elif isinstance(x, time):
            x = datetime.combine(date.today(), x)

        if not x.tzinfo:
            x = x.replace(tzinfo=self._localtimezone)
        return x


class Database:
    """
    This class is essentially a wrapper around a directory which contains a
    bunch of ical files. While not a traditional SQL database, it's still *our*
    database.
    """

    def __init__(self, path):
        self.path = path

    @cached_property
    def todos(self):
        """
        Returns a map of TODOs, where each key is the filename, and value a
        Todo object.
        """
        rv = {}

        for entry in os.listdir(self.path):
            if not entry.endswith(".ics"):
                continue
            with open(os.path.join(self.path, entry), 'rb') as f:
                try:
                    cal = f.read()
                    if b'\nBEGIN:VTODO' not in cal:
                        continue
                    cal = icalendar.Calendar.from_ical(cal)
                    for component in cal.walk('VTODO'):
                        rv[entry] = Todo(component, entry)
                except Exception as e:
                    logger.warn("Failed to read entry %s: %s.", entry, e)

        return rv

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
                f.write(c.to_ical().decode("UTF-8"))

    def delete(self, todo):
        path = os.path.join(self.path, todo.filename)
        os.remove(path)

    @cached_property
    def name(self):
        try:
            with open(os.path.join(self.path, 'displayname')) as f:
                return f.read().strip()
        except (OSError, IOError):
            return split(normpath(self.path))[1]

    @cached_property
    def color_raw(self):
        '''
        The color is a file whose content is of the format `#RRGGBB`.
        '''

        try:
            with open(os.path.join(self.path, 'color')) as f:
                return f.read().strip()
        except (OSError, IOError):
            pass

    @cached_property
    def color_rgb(self):
        rv = self.color_raw
        if rv:
            return _parse_color(rv)

    @cached_property
    def color_ansi(self):
        rv = self.color_rgb
        if rv:
            return rgb8(*rv)

    def __str__(self):
        return self.name


def _parse_color(color):
    if not color.startswith('#'):
        return

    r = color[1:3]
    g = color[3:5]
    b = color[5:8]

    if len(r) == len(g) == len(b) == 2:
        return int(r, 16), int(g, 16), int(b, 16)
