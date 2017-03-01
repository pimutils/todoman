import logging
import os
import socket
import sqlite3
from datetime import date, datetime, time, timedelta
from os.path import normpath, split
from uuid import uuid4

import dateutil.parser
import icalendar
from atomicwrites import AtomicWriter
from dateutil.tz import tzlocal

logger = logging.getLogger(name=__name__)


class NoSuchTodo(Exception):
    pass


class UnsafeOperationException(Exception):
    """
    Raised when attempting to perform an unsafe operation.

    Typical examples of unsafe operations are attempting to save a
    partially-loaded todo.
    """
    pass


class AlreadyExists(Exception):
    """
    Raise when two objects have a same identity.

    This can ocurrs when two lists have the same name, or when two Todos have
    the same path.
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

    def __init__(self, todo=None, filename=None, mtime=None, new=False):
        """
        Creates a new todo using `todo` as a source.

        :param icalendar.Todo todo: The icalendar component object on which
        this todo is based, if applicable.
        :param str filename: The name of the file for this todo. Defaults to
        the <uid>.ics
        :param mtime int: The last modified time for the file backing this
        Todo.
        :param bool new: Indicate that a new Todo is being created and should
        be populated with default values.
        """

        if todo:
            self.todo = todo
        else:
            self.todo = icalendar.Todo()

        if new:
            now = datetime.now(self._localtimezone)
            uid = uuid4().hex + socket.gethostname()
            self.todo.add('uid', uid)
            self.todo.add('percent-complete', 0)
            self.todo.add('priority', 0)
            self.todo.add('created', now)

        if self.todo.get('dtstamp', None) is None:
            self.todo.add('dtstamp', datetime.utcnow())

        self.filename = filename or "{}.ics".format(self.todo.get('uid'))
        if os.path.basename(self.filename) != self.filename:
            raise ValueError('Must not be an absolute path: {}'
                             .format(self.filename))
        self.mtime = mtime or datetime.now()

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
        else:
            x = x.astimezone(self._localtimezone)
        return x

    @property
    def list(self):
        return self._list

    @list.setter
    def list(self, list_):
        self._list = list_

    def save(self):
        raise UnsafeOperationException()


class FileTodo(Todo):
    """
    A Todo backed by a file

    This model represents a Todo loaded and backed by a file. Saving it is a
    valid operation.
    """

    def __init__(self, new=True, **kwargs):
        super().__init__(new=new, **kwargs)

    @classmethod
    def from_file(cls, path, id=None):
        with open(path, 'rb') as f:
            cal = f.read()
            cal = icalendar.Calendar.from_ical(cal)
            try:
                component = cal.walk('VTODO')[0]
                todo = cls(
                    new=False,
                    todo=component,
                    filename=os.path.basename(path),
                )
                todo.id = id
                return todo
            except IndexError:
                pass

    def save(self, list_=None):
        list_ = list_ or self.list
        path = os.path.join(list_.path, self.filename)
        assert path.startswith(list_.path)
        sequence = self.todo.get('SEQUENCE', 0)
        self.todo['SEQUENCE'] = sequence + 1
        if os.path.exists(path):
            # Update an existing entry:
            with open(path, 'rb') as f:
                cal = icalendar.Calendar.from_ical(f.read())
                for index, component in enumerate(cal.subcomponents):
                    if component.get('uid', None) == self.uid:
                        cal.subcomponents[index] = self.todo

            with AtomicWriter(path, overwrite=True).open() as f:
                f.write(cal.to_ical().decode("UTF-8"))
        else:
            # Save a new entry:
            c = icalendar.Calendar()
            c.add('prodid', 'io.barrera.todoman')
            c.add('version', '2.0')
            c.add_component(self.todo)

            with AtomicWriter(path).open() as f:
                f.write(c.to_ical().decode("UTF-8"))


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

    SCHEMA_VERSION = 2

    def __init__(self, path):
        self.cache_path = str(path)
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        self._conn = sqlite3.connect(self.cache_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

        self.create_tables()

    def save_to_disk(self):
        self._conn.commit()

    def is_latest_version(self):
        """Checks if the cache DB schema is the latest version."""
        try:
            return self._conn.execute(
                'SELECT version FROM meta WHERE version = ?',
                (Cache.SCHEMA_VERSION,),
            ).fetchone()
        except sqlite3.OperationalError:
            return False

    def create_tables(self):
        if self.is_latest_version():
            return

        self._conn.executescript('''
            DROP TABLE IF EXISTS lists;
            DROP TABLE IF EXISTS files;
            DROP TABLE IF EXISTS todos;
        ''')

        self._conn.execute(
            'CREATE TABLE IF NOT EXISTS meta ("version" INT)'
        )

        self._conn.execute(
            'INSERT INTO meta (version) VALUES (?)',
            (Cache.SCHEMA_VERSION,),
        )

        self._conn.execute('''
            CREATE TABLE IF NOT EXISTS lists (
                "name" TEXT PRIMARY KEY,
                "path" TEXT,
                "colour" TEXT,
                CONSTRAINT path_unique UNIQUE (path)
            );
        ''')

        self._conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                "path" TEXT PRIMARY KEY,
                "list_name" TEXT,
                "mtime" INTEGER,

                CONSTRAINT path_unique UNIQUE (path),
                FOREIGN KEY(list_name) REFERENCES lists(name) ON DELETE CASCADE
            );
        ''')

        self._conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                "file_path" TEXT,

                "id" INTEGER PRIMARY KEY,
                "uid" TEXT,
                "summary" TEXT,
                "due" INT,
                "priority" INTEGER,
                "created_at" TEXT,
                "completed_at" TEXT,
                "percent_complete" INTEGER,
                "dtstamp" TEXT,
                "status" TEXT,
                "description" TEXT,
                "location" TEXT,
                "categories" TEXT,

                CONSTRAINT file_unique UNIQUE (file_path),
                FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
            );
        ''')

    def clear(self):
        self._conn.close()
        os.remove(self.cache_path)
        self._conn = None

    def add_list(self, name, path, colour):
        """
        Inserts a new list into the cache.

        Returns the id of the newly inserted list.
        """

        result = self._conn.execute(
            'SELECT name FROM lists WHERE path = ?',
            (path,),
        ).fetchone()

        if result:
            return result['name']

        try:
            self._conn.execute(
                "INSERT INTO lists (name, path, colour) VALUES (?, ?, ?)",
                (name, path, colour,),
            )
        except sqlite3.IntegrityError as e:
            raise AlreadyExists(name) from e

        return self.add_list(name, path, colour)

    def add_file(self, list_name, path, mtime):
        try:
            self._conn.execute('''
                INSERT INTO files (
                    list_name,
                    path,
                    mtime
                ) VALUES (?, ?, ?);
                ''', (
                list_name,
                path,
                mtime,
            ))
        except sqlite3.IntegrityError as e:
            raise AlreadyExists(list_name) from e

    def add_todo(self, todo, file_path):
        """
        Adds a todo into the cache.

        :param icalendar.Todo todo: The icalendar component object on which
        """

        sql = '''
            INSERT INTO todos (
                file_path,
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
            '''

        params = (
            file_path,
            todo.uid,
            todo.summary,
            todo.due.timestamp() if todo.due else None,
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

        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            rv = cursor.lastrowid
        finally:
            cursor.close()

        return rv

    def todos(self, all=False, lists=[], priority=None, location='',
              category='', grep='', sort=[], reverse=True, due=None,
              done_only=None, start=None):
        """
        Returns filtered cached todos, in a specified order.

        If no order is specified, todos are sorted by the following fields::

            completed_at
            -priority
            due
            -created_at

        :param bool all: If true, also return completed todos.
        :param list lists: Only return todos for these lists.
        :param str location: Only return todos with a location containing this
            string.
        :param str category: Only return todos with a category containing this
            string.
        :param str grep: Filter common fields with this substring.
        :param list sort: Order returned todos by these fields. Field names
            with a ``-`` prepended will be used to sort in reverse order.
        :param bool reverse: Reverse the order of the todos after sorting.
        :param int due: Return only todos due within ``due`` hours.
        :param str priority: Only return todos with priority at least as
            high as specified.
        :param bool done_only: If true, return done tasks, else incomplete
            tasks
        :param start: Return only todos before/after ``start`` date
        :return: A sorted, filtered list of todos.
        :rtype: generator
        """
        list_map = {list.name: list for list in self.lists()}

        extra_where = []
        params = []

        if not all:
            # XXX: Duplicated logic of Todo.is_completed
            if done_only:
                extra_where.append('AND status == "COMPLETED"')
            else:
                extra_where.append('AND completed_at is NULL '
                                   'AND status != "CANCELLED" '
                                   'AND status != "COMPLETED"')
        if lists:
            lists = [l.name if isinstance(l, List) else l for l in lists]
            q = ', '.join(['?'] * len(lists))
            extra_where.append('AND files.list_name IN ({})'.format(q))
            params.extend(lists)
        if priority:
            extra_where.append('AND PRIORITY > 0 AND PRIORITY <= ?')
            params.append('{}'.format(priority))
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
        if due:
            max_due = (datetime.now() + timedelta(hours=due)).timestamp()
            extra_where.append('AND due IS NOT NULL AND due < ?')
            params.append(max_due)
        if start:
            is_before, dt = start
            if is_before:
                extra_where.append('AND created_at <= ?')
                params.append(dt)
            else:
                extra_where.append('AND created_at >= ?')
                params.append(dt)
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
              SELECT todos.*, files.list_name, files.path
                FROM todos, files
               WHERE todos.file_path = files.path {}
            ORDER BY {}
        '''.format(' '.join(extra_where), order,)
        result = self._conn.execute(query, params)

        for row in result:
            todo = Todo()
            todo.id = row['id']
            todo.uid = row['uid']
            todo.summary = row['summary']
            if row['due']:
                todo.due = datetime.fromtimestamp(row['due'])
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
            todo.list = list_map[row['list_name']]
            todo.filename = os.path.basename(row['path'])
            yield todo

    def lists(self):
        result = self._conn.execute("SELECT * FROM lists")
        for row in result:
            yield List(
                name=row['name'],
                path=row['path'],
                colour=row['colour'],
            )

    def list(self, name):
        row = self._conn.execute(
            "SELECT * FROM lists WHERE name = ?",
            (name,),
        ).fetchone()

        return List(
            name=row['name'],
            path=row['path'],
            colour=row['colour'],
        )

    def expire_lists(self, paths):
        results = self._conn.execute("SELECT path, name from lists")
        for result in results:
            if result['path'] not in paths:
                self.delete_list(result['name'])

    def delete_list(self, name):
        self._conn.execute("DELETE FROM lists WHERE lists.name = ?", (name,))

    def todo(self, id):
        result = self._conn.execute('''
            SELECT files.path, list_name
              FROM files, todos
             WHERE files.path = todos.file_path
               AND todos.id = ?
        ''', (id,),
        ).fetchone()

        if not result:
            raise NoSuchTodo()

        path = result['path']
        todo = FileTodo.from_file(path, id)
        assert todo is not None
        todo.list = self.list(result['list_name'])

        return todo

    def expire_files(self, paths_to_mtime):
        """Remove stale cache entries based on the given fresh data."""
        result = self._conn.execute("SELECT path, mtime FROM files")
        for row in result:
            path, mtime = row['path'], row['mtime']
            if paths_to_mtime.get(path, None) != mtime:
                self.expire_file(path)

    def expire_file(self, path):
        self._conn.execute("DELETE FROM files WHERE path = ?", (path,))


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
        self.paths = [str(path) for path in paths]
        self.update_cache()

    def update_cache(self):
        self.cache.expire_lists(self.paths)

        paths_to_mtime = {}
        paths_to_list_name = {}

        for path in self.paths:
            list_name = self.cache.add_list(
                self._list_name(path),
                path,
                self._list_colour(path),
            )
            for entry in os.listdir(path):
                if not entry.endswith('.ics'):
                    continue
                entry_path = os.path.join(path, entry)
                mtime = _getmtime(entry_path)
                paths_to_mtime[entry_path] = mtime
                paths_to_list_name[entry_path] = list_name

        self.cache.expire_files(paths_to_mtime)

        for entry_path, mtime in paths_to_mtime.items():
            list_name = paths_to_list_name[entry_path]
            try:
                self.cache.add_file(list_name, entry_path, mtime)
            except AlreadyExists:
                continue

            try:
                todo = FileTodo.from_file(entry_path)
                if todo:
                    self.cache.add_todo(todo, entry_path)
            except Exception as e:
                logger.exception("Failed to read entry %s.", entry_path)

        self.cache.save_to_disk()

    def todos(self, **kwargs):
        return self.cache.todos(**kwargs)

    def todo(self, id):
        return self.cache.todo(id)

    def lists(self):
        return self.cache.lists()

    def move(self, todo, new_list, from_list=None):
        from_list = from_list or todo.list
        orig_path = os.path.join(from_list.path, todo.filename)
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

    def flush(self):
        for todo in self.todos(all=True):
            if todo.is_completed:
                yield todo
                self.delete(todo)

        self.cache.clear()
        self.cache = None

    def save(self, todo, list_):
        todo.save(list_)
        path = os.path.join(list_.path, todo.filename)
        self.cache.expire_file(path)
        mtime = _getmtime(path)
        self.cache.add_file(list_.name, path, mtime)
        id = self.cache.add_todo(todo, path)
        self.cache.save_to_disk()
        todo.id = id


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
