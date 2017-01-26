import logging
import os
import socket
import sqlite3
from datetime import date, datetime, time, timedelta
from os.path import normpath, split
from uuid import uuid4

import icalendar
import dateutil.parser
import sqlitebck
from atomicwrites import AtomicWriter
from dateutil.tz import tzlocal

logger = logging.getLogger(name=__name__)
# logger.addHandler(logging.FileHandler('model.log'))


class NoSuchTodo(Exception):
    pass


class UnsafeOperationException(Exception):
    """
    Raised when attempting to perform an unsafe operation.

    Typical examples of unsafe operations are attempting to save a
    partially-loaded todo.
    """
    pass


class cached_property:  # noqa
    '''A read-only @property that is only evaluated once. Only usable on class
    instances' methods.
    '''
    def __init__(self, fget, doc=None):
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        self.__doc__ = doc or fget.__doc__
        self.fget = fget

    def __get__(self, obj, cls):
        if obj is None:
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

    def __init__(self, todo=None, filename=None, mtime=None, safe=False,
                 new=True):
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

        if not todo and new:
            now = datetime.now(self._localtimezone)
            uid = uuid4().hex + socket.gethostname()
            self.todo.add('uid', uid)
            self.todo.add('due', now + timedelta(days=1))
            self.todo.add('percent-complete', 0)
            self.todo.add('priority', 0)
            self.todo.add('created', now)

        if self.todo.get('dtstamp', None) is None:
            self.todo.add('dtstamp', datetime.utcnow())

        self.safe = safe or new
        self.filename = filename or "{}.ics".format(self.todo.get('uid'))
        self.mtime = mtime or datetime.now()

    @staticmethod
    def from_file(path):
        with open(path, 'rb') as f:
            cal = f.read()
            if b'\nBEGIN:VTODO' in cal:
                cal = icalendar.Calendar.from_ical(cal)

                # Note: Syntax is weird due to icalendar API, and the fact that
                # we only support one TODO per file.
                for component in cal.walk('VTODO'):
                    return Todo(component, path)

    def _set_field(self, name, value):
        if name in self.todo:
            del(self.todo[name])
        # We want to save things like [] or 0, but not null, or nullstrings
        if value is not None and value is not '':
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
    def categories(self):
        categories = self.todo.get('categories', '').split(',')
        return tuple(filter(None, categories))

    @property
    def raw_categories(self):
        return self.todo.get('categories', '')

    @categories.setter
    def categories(self, categories):
        self._set_field('categories', ','.join(categories))

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
    def start(self):
        """
        Returns the dtstart date, as a datetime object, if set, or None.
        """
        if self.todo.get('dtstart', None) is None:
            return None
        else:
            return self._normalize_datetime(self.todo.decoded('dtstart'))

    @start.setter
    def start(self, dtstart):
        self._set_field('dtstart', dtstart)

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
        self._set_field('percent-complete', percent_complete)

    @property
    def priority(self):
        return self.todo.get('priority', 0)

    @priority.setter
    def priority(self, priority):
        self._set_field('priority', priority)

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

    @uid.setter
    def uid(self, uid):
        self._set_field('uid', uid)

    @property
    def dtstamp(self):
        return self.todo.decoded('dtstamp')

    @dtstamp.setter
    def dtstamp(self, dtstamp):
        self._set_field('dtstamp', dtstamp)

    def _normalize_datetime(self, x):
        '''
        Eliminate several differences between dates, times and datetimes which
        are hindering comparison:

        - Convert everything to datetime
        - Add missing timezones
        '''
        if isinstance(x, date) and not isinstance(x, datetime):
            x = datetime(x.year, x.month, x.day)
        elif isinstance(x, time):
            x = datetime.combine(date.today(), x)

        if not x.tzinfo:
            x = x.replace(tzinfo=self._localtimezone)
        return x

    @property
    def list(self):
        return self._list

    @list.setter
    def list(self, list_):
        self._list = list_


class CachedTodo:

    def __init__(self, cached_data):
        pass


class Cache:
    """
    Caches Todos for faster read and simpler querying interface

    The Cache class persists relevant[1] fields into an SQL database, which is
    only updated if the actual file has been modified. This greatly increases
    load times, but, more importantly, provides a simpler interface for
    filtering/querying/sorting.

    The internal sqlite database is copied fully into memory at startup, and
    dumped again at showdown. This reduces excesive disk I/O.

    [1]: Relevent fields are those we show when listing todos, or those which
    may be used for filtering/sorting.
    """

    def __init__(self, path):
        self.cache_path = path

        self.conn = sqlite3.connect(
            ':memory:',
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self.conn.row_factory = sqlite3.Row
        self.load_from_disk()
        self.cur = self.conn.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")

        self.create_tables()

    def load_from_disk(self):
        conn_disk = sqlite3.connect(
            self.cache_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        sqlitebck.copy(conn_disk, self.conn)
        conn_disk.close()

    def save_to_disk(self):
        conn_disk = sqlite3.connect(
            self.cache_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        sqlitebck.copy(self.conn, conn_disk)
        conn_disk.close()

    def create_tables(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                "id" INTEGER PRIMARY KEY,
                "name" TEXT,
                "path" TEXT,
                "colour" TEXT,
                CONSTRAINT name_unique UNIQUE (name),
                CONSTRAINT path_unique UNIQUE (path)
            );
        ''')

        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS files (
                "id" INTEGER PRIMARY KEY,
                "list_id" INTEGER,
                "path" TEXT,
                "mtime" TEXT,

                CONSTRAINT path_unique UNIQUE (path),
                FOREIGN KEY(list_id) REFERENCES lists(id) ON DELETE CASCADE
            );
        ''')

        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                "file_id" INTEGER,

                "id" INTEGER PRIMARY KEY,
                "uid" TEXT,
                "summary" TEXT,
                "due" TEXT,
                "priority" INTEGER,
                "created_at" TEXT,
                "completed_at" TEXT,
                "percent_complete" INTEGER,
                "dtstamp" TEXT,
                "status" TEXT,
                "description" TEXT,
                "location" TEXT,
                "categories" TEXT,

                CONSTRAINT file_unique UNIQUE (file_id),
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            );
        ''')

        self.conn.commit()

    def add_list(self, name, path, colour):
        """
        Inserts a new list into the cache.

        Returns the id of the newly inserted list.
        """

        result = self.cur.execute(
            'SELECT id FROM lists WHERE path = ?',
            (path,),
        ).fetchone()

        if result:
            return result['id']

        try:
            self.cur.execute(
                "INSERT INTO lists (name, path, colour) VALUES (?, ?, ?)",
                (name, path, colour,),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise Exception('Multiple lists named "{}"'.format(name)) from e

        return self.add_list(name, path, colour)

    def add_file(self, list_id, path, mtime):
        self.cur.execute('''
            INSERT OR IGNORE INTO files (
                list_id,
                path,
                mtime
            ) VALUES (?, ?, ?);
            ''', (
            list_id,
            path,
            mtime,
        ))
        self.conn.commit()

        result = self.cur.execute(
            'SELECT id FROM files WHERE path = ?',
            (path,),
        ).fetchone()

        return result['id']

    def add_todo(self, todo, file_id):
        """
        Adds a todo into the cache.

        :param icalendar.Todo todo: The icalendar component object on which
        """

        self.cur.execute('''
            INSERT INTO todos (
                file_id,
                uid,
                summary,
                due,
                priority,
                created_at,
                completed_at,
                percent_complete,
                dtstamp,
                status,
                description,
                location,
                categories
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_id,
                todo.uid,
                todo.summary,
                todo.due,
                todo.priority,
                todo.created_at,
                todo.completed_at,
                todo.percent_complete,
                todo.dtstamp,
                todo.status,
                todo.description,
                todo.location,
                todo.raw_categories,
            )
        )

        self.conn.commit()

    def todos(self, all=False, lists=[], urgent=False, location='',
              category='', grep='', sort=[], reverse=False):
        todos = []
        list_map = self._lists_map()

        extra_where = []
        params = []

        if not all:
            extra_where.append('AND completed_at is NULL')
        if lists:
            q = ', '.join(['?'] * len(lists))

            query = 'SELECT id FROM lists WHERE name IN ({});'.format(q)
            list_ids = [row['id'] for row in self.conn.execute(q, lists)]
            extra_where.append('AND files.list_id IN ({})'.format(q))
            params.extend(list_ids)
        if urgent:
            extra_where.append('AND priority = 9')
        if location:
            extra_where.append('AND location LIKE ?')
            params.append('%{}%'.format(location))
        if category:
            extra_where.append('AND categories LIKE ?')
            params.append('%{}%'.format(category))
        if grep:
            # # requires sqlite with pcre, which won't be availabel everywhere:
            # extra_where.append('AND summary REGEXP ?')
            # params.append(grep)
            extra_where.append('AND summary LIKE ?')
            params.append('%{}%'.format(grep))

        if sort:
            order = []
            for s in sort:
                if s.startswith('-'):
                    order.append(' {} ASC'.format(s[1:]))
                else:
                    order.append(' {} DESC'.format(s))
            order = ','.join(order)
        else:
            order = '''
                completed_at DESC,
                priority ASC,
                due IS NOT NULL, due DESC,
                created_at ASC
            '''

        if not reverse:
            # Note the change in case to avoid swapping all of them. sqlite
            # doesn't care about casing anyway.
            order = order.replace(' DESC', ' asc').replace(' ASC', ' desc')

        query = '''
              SELECT todos.*, files.list_id
                FROM todos, files
               WHERE todos.file_id = files.id {}
            ORDER BY {}
        '''.format(' '.join(extra_where), order,)
        result = self.conn.execute(query, params)

        for row in result:
            todo = Todo(new=False, safe=False)
            todo.id = row['id']
            todo.uid = row['uid']
            todo.summary = row['summary']
            if row['due']:
                todo.due = dateutil.parser.parse(row['due'])
            todo.priority = row['priority']
            if row['created_at']:
                todo.created_at = dateutil.parser.parse(row['created_at'])
            if row['completed_at']:
                todo.completed_at = dateutil.parser.parse(row['completed_at'])
            if row['dtstamp']:
                todo.dtstamp = dateutil.parser.parse(row['dtstamp'])
            todo.percent_complete = row['percent_complete']
            todo.status = row['status']
            todo.description = row['description']
            todo.location = row['location']
            todo.list = list_map[row['list_id']]
            todos.append(todo)

        return todos

    def _lists_map(self):
        lists = {}

        result = self.conn.execute("SELECT * FROM lists")
        for row in result:
            list_ = List(
                name=row['name'],
                path=row['path'],
                colour=row['colour'],
            )
            lists[row['id']] = list_

        return lists

    def lists(self):
        lists = []

        result = self.conn.execute("SELECT * FROM lists")
        for row in result:
            lists.append(List(
                name=row['name'],
                path=row['path'],
                colour=row['colour'],
            ))

        return lists

    def list(self, id):
        row = self.conn.execute(
            "SELECT * FROM lists WHERE ID = ?",
            (id,),
        ).fetchone()

        return List(
            name=row['name'],
            path=row['path'],
            colour=row['colour'],
        )

    def revalidate_lists(self, paths):
        results = self.conn.execute("SELECT path, id from lists")
        for result in results:
            if result['path'] not in paths:
                self.delete_list(result['id'])

    def delete_list(self, id):
        self.conn.execute("DELETE FROM lists WHERE lists.id = ?", (id,))
        self.conn.commit()

    def todo(self, id):
        result = self.cur.execute('''
            SELECT files.path, list_id
              FROM files, todos
             WHERE files.id = todos.file_id
               AND todos.id = ?
        ''', (id,),
        ).fetchone()

        if not result:
            raise NoSuchTodo()

        path = result['path']
        todo = Todo.from_file(path)
        todo.list = self.list(result['list_id'])

        return todo

    def revalidate(self, path, mtime):
        """
        Returns True if a path/mtime pair is still valid

        Returns True if a path/mtime pair is still valid in the cache,
        otherwise, purges them, and returns False.
        """
        row = self.conn.execute(
            "SELECT mtime FROM files WHERE path = ?",
            (path,)
        ).fetchone()
        if row is None:
            return False
        if int(row['mtime']) == mtime:
            return True

        self._invalidate_file(path)
        return False

    def _invalidate_file(self, path):
        row = self.cur.execute(
            "SELECT id FROM files WHERE path = ?",
            (path,),
        ).fetchone()

        if row is None:
            return

        file_id = row['id']

        self.cur.execute(
            "DELETE FROM todos WHERE file_id = ?",
            (file_id,),
        )
        self.cur.execute(
            "DELETE FROM files WHERE id = ?",
            (file_id,),
        )
        self.conn.commit()


class List:

    def __init__(self, name, path, colour=None):
        self.name = name
        self.path = path
        self.colour = colour

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
            return '\33[38;2;{!s};{!s};{!s}m'.format(*rv)

    def __str__(self):
        return self.name


class Database:
    """
    This class is essentially a wrapper around all the lists (which in turn,
    contain all the todos).

    Caching in abstracted inside this class, and is transparent to outside
    classes.
    """

    def __init__(self, paths, cache_path):
        self.cache = Cache(cache_path)

        self.cache.revalidate_lists(paths)

        for path in paths:
            self._cache_list(path)
            self.cache.save_to_disk()

    def _cache_list(self, path):
        """
        Returns a map of TODOs, where each key is the filename, and value a
        Todo object.
        """
        list_id = self.cache.add_list(
            self._list_name(path),
            path,
            self._list_colour(path),
        )

        for entry in os.listdir(path):
            if not entry.endswith(".ics"):
                continue
            entry_path = os.path.join(path, entry)
            mtime = _getmtime(entry_path)

            if self.cache.revalidate(entry_path, mtime):
                continue

            file_id = self.cache.add_file(list_id, entry_path, mtime)

            try:
                todo = Todo.from_file(entry_path)
                if todo:
                    self.cache.add_todo(todo, file_id)
            except Exception as e:
                logger.exception("Failed to read entry %s.", entry)

    def todos(self, **kwargs):
        return self.cache.todos(**kwargs)

    def todo(self, id):
        return self.cache.todo(id)

    def lists(self):
        return self.cache.lists()

    def save(self, todo):
        if not todo.safe:
            raise UnsafeOperationException()

        path = os.path.join(todo.list.path, todo.filename)

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

    def move(self, todo, new_list):
        orig_path = os.path.join(todo.list.path, todo.filename)
        dest_path = os.path.join(new_list.path, todo.filename)

        os.rename(orig_path, dest_path)

    def delete(self, todo):
        path = os.path.join(todo.list.path, todo.filename)
        os.remove(path)

    def _list_name(self, path):
        try:
            with open(os.path.join(path, 'displayname')) as f:
                return f.read().strip()
        except (OSError, IOError):
            return split(normpath(path))[1]

    def _list_colour(self, path):
        '''
        The color is a file whose content is of the format `#RRGGBB`.
        '''

        try:
            with open(os.path.join(path, 'color')) as f:
                return f.read().strip()
        except (OSError, IOError):
            pass


def _parse_color(color):
    if not color.startswith('#'):
        return

    r = color[1:3]
    g = color[3:5]
    b = color[5:8]

    if len(r) == len(g) == len(b) == 2:
        return int(r, 16), int(g, 16), int(b, 16)


def _getmtime(path):
    stat = os.stat(path)
    return getattr(stat, 'st_mtime_ns', stat.st_mtime)
