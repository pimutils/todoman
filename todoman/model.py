from __future__ import annotations

import logging
import os
import socket
import sqlite3
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from functools import cached_property
from os.path import normpath
from os.path import split
from typing import Iterable
from uuid import uuid4

import icalendar
import pytz
from atomicwrites import AtomicWriter
from dateutil.rrule import rrulestr
from dateutil.tz import tzlocal

from todoman import exceptions

logger = logging.getLogger(name=__name__)

# Initialize this only once
# We were doing this all over the place (even if unused!), so at least only do
# it once.
LOCAL_TIMEZONE = tzlocal()


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

    categories: list[str]
    completed_at: datetime | None
    created_at: datetime | None
    due: date | None
    dtstamp: datetime | None
    last_modified: datetime | None
    related: list[Todo]
    rrule: str | None
    start: date | None

    def __init__(
        self,
        filename: str | None = None,
        mtime: int | None = None,
        new: bool = False,
        list: TodoList | None = None,
    ):
        """
        Creates a new todo using `todo` as a source.

        :param str filename: The name of the file for this todo. Defaults to
            the <uid>.ics
        :param mtime int: The last modified time for the file backing this
            Todo.
        :param bool new: Indicate that a new Todo is being created and should
            be populated with default values.
        :param TodoList list: The list to which this Todo belongs.
        """
        self.list = list
        now = datetime.now(LOCAL_TIMEZONE)
        self.uid = f"{uuid4().hex}@{socket.gethostname()}"

        if new:
            self.created_at = now
        else:
            self.created_at = None

        # Default values for supported fields
        self.categories = []
        self.completed_at = None
        self.description = ""
        self.dtstamp = now
        self.due = None
        self.id = None
        self.last_modified = None
        self.location = ""
        self.percent_complete = 0
        self.priority = 0
        self.rrule = ""
        self.sequence = 0
        self.start = None
        self.status = "NEEDS-ACTION"
        self.summary = ""

        self.filename = filename or f"{self.uid}.ics"
        self.related = []

        if os.path.basename(self.filename) != self.filename:
            raise ValueError(f"Must not be an absolute path: {self.filename}")
        self.mtime = mtime or datetime.now()

    def clone(self) -> Todo:
        """
        Returns a clone of this todo

        Returns a copy of this todo, which is almost identical, except that is
        has a different UUID and filename.
        """
        todo = Todo(new=True, list=self.list)

        fields = (
            Todo.STRING_FIELDS
            + Todo.INT_FIELDS
            + Todo.LIST_FIELDS
            + Todo.DATETIME_FIELDS
        )
        fields.remove("uid")

        for field in fields:
            setattr(todo, field, getattr(self, field))

        return todo

    STRING_FIELDS = [
        "description",
        "location",
        "status",
        "summary",
        "uid",
        "rrule",
    ]
    INT_FIELDS = [
        "percent_complete",
        "priority",
        "sequence",
    ]
    LIST_FIELDS = [
        "categories",
    ]
    DATETIME_FIELDS = [
        "completed_at",
        "created_at",
        "dtstamp",
        "start",
        "due",
        "last_modified",
    ]
    RRULE_FIELDS = [
        "rrule",
    ]
    ALL_SUPPORTED_FIELDS = (
        DATETIME_FIELDS + INT_FIELDS + LIST_FIELDS + RRULE_FIELDS + STRING_FIELDS
    )

    VALID_STATUSES = (
        "CANCELLED",
        "COMPLETED",
        "IN-PROCESS",
        "NEEDS-ACTION",
    )

    def __setattr__(self, name: str, value):
        """Check type and avoid setting fields to None"""
        """when that is not a valid attribue."""

        v = value

        if name in Todo.RRULE_FIELDS:
            if value is None:
                v = ""
            else:
                assert isinstance(
                    value, str
                ), f"Got {type(value)} for {name} where str was expected"

        if name in Todo.STRING_FIELDS:
            if value is None:
                v = ""
            else:
                assert isinstance(
                    value, str
                ), f"Got {type(value)} for {name} where str was expected"

        if name in Todo.INT_FIELDS:
            if value is None:
                v = 0
            else:
                assert isinstance(
                    value, int
                ), f"Got {type(value)} for {name} where int was expected"

        if name in Todo.LIST_FIELDS:
            if value is None:
                v = []
            else:
                assert isinstance(
                    value, list
                ), f"Got {type(value)} for {name} where list was expected"

        return object.__setattr__(self, name, v)

    @property
    def is_completed(self) -> bool:
        return bool(self.completed_at) or self.status in ("CANCELLED", "COMPLETED")

    @property
    def is_recurring(self) -> bool:
        return bool(self.rrule)

    def _apply_recurrence_to_dt(self, dt) -> datetime | None:
        if not dt:
            return None

        recurrence = rrulestr(self.rrule, dtstart=dt)

        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, time.min)

        return recurrence.after(dt)

    def _create_next_instance(self):
        copy = self.clone()
        copy.due = self._apply_recurrence_to_dt(self.due)
        copy.start = self._apply_recurrence_to_dt(self.start)

        assert copy.uid != self.uid

        # TODO: Push copy's alarms.
        return copy

    def complete(self) -> None:
        """
        Immediately completes this todo

        Immediately marks this todo as completed, sets the percentage to 100%
        and the completed_at datetime to now.

        If this todo belongs to a series, newly created todo are added to the
        ``related`` list.
        """
        if self.is_recurring:
            related = self._create_next_instance()
            if related:
                self.rrule = None
                self.related.append(related)

        self.completed_at = datetime.now(tz=LOCAL_TIMEZONE)
        self.percent_complete = 100
        self.status = "COMPLETED"

    @cached_property
    def path(self) -> str:
        if not self.list:
            raise ValueError("A todo without a list does not have a path.")

        return os.path.join(self.list.path, self.filename)

    def cancel(self) -> None:
        self.status = "CANCELLED"


class VtodoWriter:
    """Writes a Todo as a VTODO file."""

    """Maps Todo field names to VTODO field names"""
    FIELD_MAP = {
        "summary": "summary",
        "priority": "priority",
        "sequence": "sequence",
        "uid": "uid",
        "categories": "categories",
        "completed_at": "completed",
        "description": "description",
        "dtstamp": "dtstamp",
        "start": "dtstart",
        "due": "due",
        "location": "location",
        "percent_complete": "percent-complete",
        "status": "status",
        "created_at": "created",
        "last_modified": "last-modified",
        "rrule": "rrule",
    }

    def __init__(self, todo: Todo):
        self.todo = todo

    def normalize_datetime(self, dt: date) -> date:
        """
        Eliminate several differences between dates, times and datetimes which
        are hindering comparison:

        - Convert everything to datetime
        - Add missing timezones
        - Cast to UTC

        Datetimes are cast to UTC because icalendar doesn't include the
        VTIMEZONE information upon serialization, and some clients have issues
        dealing with that.
        """
        if isinstance(dt, date) and not isinstance(dt, datetime):
            return dt

        if not dt.tzinfo:
            dt = dt.replace(tzinfo=LOCAL_TIMEZONE)

        return dt.astimezone(pytz.UTC)

    def serialize_field(self, name: str, value):
        if name in Todo.RRULE_FIELDS:
            return icalendar.vRecur.from_ical(value)
        if name in Todo.DATETIME_FIELDS:
            return self.normalize_datetime(value)
        if name in Todo.LIST_FIELDS:
            return value
        if name in Todo.INT_FIELDS:
            return int(value)
        if name in Todo.STRING_FIELDS:
            return value

        raise Exception(f"Unknown field {name} serialized.")

    def set_field(self, name: str, value):
        # If serialized value is None:
        self.vtodo.pop(name)
        if value:
            logger.debug("Setting field %s to %s.", name, value)
            self.vtodo.add(name, value)

    def serialize(self, original=None):
        """Serialize a Todo into a VTODO."""
        if not original:
            original = icalendar.Todo()
        self.vtodo = original

        for source, target in self.FIELD_MAP.items():
            self.vtodo.pop(target)
            if getattr(self.todo, source):
                self.set_field(
                    target,
                    self.serialize_field(source, getattr(self.todo, source)),
                )

        return self.vtodo

    def _read(self, path):
        with open(path, "rb") as f:
            cal = f.read()
            cal = icalendar.Calendar.from_ical(cal)
            for component in cal.walk("VTODO"):
                return component

    def write(self):
        if os.path.exists(self.todo.path):
            self._write_existing(self.todo.path)
        else:
            self._write_new(self.todo.path)

        return self.vtodo

    def _write_existing(self, path):
        original = self._read(path)
        vtodo = self.serialize(original)

        with open(path, "rb") as f:
            cal = icalendar.Calendar.from_ical(f.read())
            for index, component in enumerate(cal.subcomponents):
                if component.get("uid", None) == self.todo.uid:
                    cal.subcomponents[index] = vtodo

        with AtomicWriter(path, "wb", overwrite=True).open() as f:
            f.write(cal.to_ical())

    def _write_new(self, path):
        vtodo = self.serialize()

        c = icalendar.Calendar()
        c.add_component(vtodo)

        with AtomicWriter(path, "wb").open() as f:
            c.add("prodid", "io.barrera.todoman")
            c.add("version", "2.0")
            f.write(c.to_ical())

        return vtodo


class Cache:
    """
    Caches Todos for faster read and simpler querying interface

    The Cache class persists relevant[1] fields into an SQL database, which is
    only updated if the actual file has been modified. This greatly increases
    load times, but, more importantly, provides a simpler interface for
    filtering/querying/sorting.

    [1]: Relevant fields are those we show when listing todos, or those which
    may be used for filtering/sorting.
    """

    SCHEMA_VERSION = 9

    def __init__(self, path: str):
        self.cache_path = str(path)
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        self._conn = sqlite3.connect(self.cache_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

        self.create_tables()

    def save_to_disk(self) -> None:
        self._conn.commit()

    def is_latest_version(self):
        """Checks if the cache DB schema is the latest version."""
        try:
            return self._conn.execute(
                "SELECT version FROM meta WHERE version = ?",
                (Cache.SCHEMA_VERSION,),
            ).fetchone()
        except sqlite3.OperationalError:
            return False

    def drop_tables(self):
        self._conn.executescript(
            """
            DROP TABLE IF EXISTS todos;
            DROP TABLE IF EXISTS lists;
            DROP TABLE IF EXISTS files;
            DROP TABLE IF EXISTS categories;
        """
        )

    def create_tables(self):
        if self.is_latest_version():
            return

        self.drop_tables()

        self._conn.execute('CREATE TABLE IF NOT EXISTS meta ("version" INT)')

        self._conn.execute(
            "INSERT INTO meta (version) VALUES (?)",
            (Cache.SCHEMA_VERSION,),
        )

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lists (
                "name" TEXT PRIMARY KEY,
                "path" TEXT,
                "colour" TEXT,
                "mtime" INTEGER,

                CONSTRAINT path_unique UNIQUE (path)
            );
        """
        )

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                "path" TEXT PRIMARY KEY,
                "list_name" TEXT,
                "mtime" INTEGER,

                CONSTRAINT path_unique UNIQUE (path),
                FOREIGN KEY(list_name) REFERENCES lists(name) ON DELETE CASCADE
            );
        """
        )

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                "todos_id" INTEGER NOT NULL,
                "category" TEXT,

                CONSTRAINT category_unique UNIQUE (todos_id,category),
                FOREIGN KEY(todos_id) REFERENCES todos(id) ON DELETE CASCADE
            );
        """
        )

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                "file_path" TEXT,

                "id" INTEGER PRIMARY KEY,
                "uid" TEXT,
                "summary" TEXT,
                "due" INTEGER,
                "due_dt" INTEGER,
                "start" INTEGER,
                "start_dt" INTEGER,
                "priority" INTEGER,
                "created_at" INTEGER,
                "completed_at" INTEGER,
                "percent_complete" INTEGER,
                "dtstamp" INTEGER,
                "status" TEXT,
                "description" TEXT,
                "location" TEXT,
                "sequence" INTEGER,
                "last_modified" INTEGER,
                "rrule" TEXT,

                FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
            );
        """
        )

    def clear(self):
        self._conn.close()
        os.remove(self.cache_path)
        self._conn = None

    def add_list(self, name: str, path: str, colour: str, mtime: int):
        """
        Inserts a new list into the cache.

        Returns the id of the newly inserted list.
        """

        result = self._conn.execute(
            "SELECT name FROM lists WHERE path = ?",
            (path,),
        ).fetchone()

        if result:
            return result["name"]

        try:
            self._conn.execute(
                """
                INSERT INTO lists (
                    name,
                    path,
                    colour,
                    mtime
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    path,
                    colour,
                    mtime,
                ),
            )
        except sqlite3.IntegrityError as e:
            raise exceptions.AlreadyExistsError("list", name) from e

        return self.add_list(name, path, colour, mtime)

    def add_file(self, list_name: str, path: str, mtime: int):
        try:
            self._conn.execute(
                """
                INSERT INTO files (
                    list_name,
                    path,
                    mtime
                ) VALUES (?, ?, ?);
                """,
                (
                    list_name,
                    path,
                    mtime,
                ),
            )
        except sqlite3.IntegrityError as e:
            raise exceptions.AlreadyExistsError("file", list_name) from e

    def add_category(self, todos_id, category):
        try:
            self._conn.execute(
                """
               INSERT INTO categories (
                   todos_id,
                   category
               ) VALUES (?, ?);
               """,
                (todos_id, category),
            )
        except sqlite3.IntegrityError as e:
            raise exceptions.AlreadyExistsError("category", category) from e

    def _serialize_datetime(
        self,
        todo: icalendar.Todo,
        field: str,
    ) -> tuple[int | None, bool | None]:
        """
        Serialize a todo field in two value, the first one is the corresponding
        timestamp, the second one is a boolean indicating if the serialized
        value is a date or a datetime.

        :param icalendar.Todo todo: An icalendar component object
        :param str field: The name of the field to serialize
        """
        dt = todo.decoded(field, None)
        if not dt:
            return None, None

        is_date = isinstance(dt, date) and not isinstance(dt, datetime)
        if is_date:
            dt = datetime(dt.year, dt.month, dt.day)

        if not dt.tzinfo:
            dt = dt.replace(tzinfo=LOCAL_TIMEZONE)
        return dt.timestamp(), is_date

    def _serialize_rrule(self, todo, field) -> str | None:
        rrule = todo.get(field)
        if not rrule:
            return None

        return rrule.to_ical().decode()

    def add_vtodo(self, todo: icalendar.Todo, file_path: str, id=None) -> int:
        """
        Adds a todo into the cache.

        :param icalendar.Todo todo: The icalendar component object on which
        """

        sql = """
            INSERT INTO todos (
                {}
                file_path,
                uid,
                summary,
                due,
                due_dt,
                start,
                start_dt,
                priority,
                created_at,
                completed_at,
                percent_complete,
                dtstamp,
                status,
                description,
                location,
                sequence,
                last_modified,
                rrule
            ) VALUES ({}?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?)
            """

        due, due_dt = self._serialize_datetime(todo, "due")
        start, start_dt = self._serialize_datetime(todo, "dtstart")

        if start and due:
            start = None if start >= due else start

        params = [
            file_path,
            todo.get("uid"),
            todo.get("summary"),
            due,
            due_dt,
            start,
            start_dt,
            todo.get("priority", 0) or None,
            self._serialize_datetime(todo, "created")[0],
            self._serialize_datetime(todo, "completed")[0],
            todo.get("percent-complete", None),
            self._serialize_datetime(todo, "dtstamp")[0],
            todo.get("status", "NEEDS-ACTION"),
            todo.get("description", None),
            todo.get("location", None),
            todo.get("sequence", 1),
            self._serialize_datetime(todo, "last-modified")[0],
            self._serialize_rrule(todo, "rrule"),
        ]

        if id:
            params = [id] + params
            sql = sql.format("id,\n", "?, ")
        else:
            sql = sql.format("", "")

        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            rv = cursor.lastrowid
            assert rv is not None
        finally:
            cursor.close()

        if todo.get("categories"):
            for category in todo.get("categories").cats:
                self.add_category(rv, category)

        return rv

    def todos(
        self,
        lists=(),
        categories=None,
        priority=None,
        location="",
        grep="",
        sort=(),
        reverse=True,
        due=None,
        start=None,
        startable=False,
        status="NEEDS-ACTION,IN-PROCESS",
    ) -> Iterable[Todo]:
        """
        Returns filtered cached todos, in a specified order.

        If no order is specified, todos are sorted by the following fields::

            completed_at
            -priority
            due
            -created_at

        :param list lists: Only return todos for these lists.
        :param str location: Only return todos with a location containing this
            string.
        :param str categories: Only return todos with a category containing this
            string.
        :param str grep: Filter common fields with this substring.
        :param list sort: Order returned todos by these fields. Field names
            with a ``-`` prepended will be used to sort in reverse order.
        :param bool reverse: Reverse the order of the todos after sorting.
        :param int due: Return only todos due within ``due`` hours.
        :param str priority: Only return todos with priority at least as
            high as specified.
        :param tuple(bool, datetime) start: Return only todos before/after
            ``start`` date
        :param list(str) status: Return only todos with any of the given
            statuses.
        :return: A sorted, filtered list of todos.
        :rtype: generator
        """
        extra_where = []
        params: list = []

        if "ANY" not in status:
            statuses = status.split(",")
            extra_where.append(
                "AND (status IN ({}) OR status IS NULL)".format(
                    ", ".join(["?"] * len(statuses))
                )
            )
            params.extend(s.upper() for s in statuses)

        if lists:
            lists = [
                list_.name if isinstance(list_, TodoList) else list_ for list_ in lists
            ]
            q = ", ".join(["?"] * len(lists))
            extra_where.append(f"AND files.list_name IN ({q})")
            params.extend(lists)
        if categories:
            category_slots = ", ".join(["?"] * len(categories))
            extra_where.append(
                "AND upper(categories.category) IN ({category_slots})".format(
                    category_slots=category_slots
                )
            )
            params = params + [category.upper() for category in categories]
        if priority:
            extra_where.append("AND PRIORITY > 0 AND PRIORITY <= ?")
            params.append(f"{priority}")
        if location:
            extra_where.append("AND location LIKE ?")
            params.append(f"%{location}%")
        if grep:
            # # requires sqlite with pcre, which won't be available everywhere:
            # extra_where.append('AND summary REGEXP ?')
            # params.append(grep)
            extra_where.append("AND summary LIKE ?")
            params.append(f"%{grep}%")
        if due:
            max_due = (datetime.now() + timedelta(hours=due)).timestamp()
            extra_where.append("AND due IS NOT NULL AND due < ?")
            params.append(max_due)
        if start:
            is_before, dt = start
            dt = dt.timestamp()
            if is_before:
                extra_where.append("AND start <= ?")
                params.append(dt)
            else:
                extra_where.append("AND start >= ?")
                params.append(dt)
        if startable:
            extra_where.append("AND (start IS NULL OR start <= ?)")
            params.append(datetime.now().timestamp())
        if sort:
            order_items = []
            for s in sort:
                if s.startswith("-"):
                    order_items.append(f" {s[1:]} ASC")
                else:
                    order_items.append(f" {s} DESC")
            order = ",".join(order_items)
        else:
            order = """
                completed_at DESC,
                priority IS NOT NULL, priority DESC,
                due IS NOT NULL, due DESC,
                created_at ASC
            """

        if not reverse:
            # Note the change in case to avoid swapping all of them. sqlite
            # doesn't care about casing anyway.
            order = order.replace(" DESC", " asc").replace(" ASC", " desc")

        query = """
        SELECT DISTINCT todos.*, files.list_name, files.path,
          group_concat(category) AS categories
        FROM todos, files
        LEFT JOIN categories
        ON categories.todos_id = todos.id
        WHERE todos.file_path = files.path {}
        GROUP BY uid
        ORDER BY {}
        """.format(
            " ".join(extra_where),
            order,
        )

        logger.debug(query)
        logger.debug(params)

        result = self._conn.execute(query, params)

        seen_paths = set()
        warned_paths = set()

        for row in result:
            todo = self._todo_from_db(row)
            path = row["path"]

            if path in seen_paths and path not in warned_paths:
                logger.warning(
                    "Todo is in read-only mode because there are multiple todos in %s",
                    path,
                )
                warned_paths.add(path)
            seen_paths.add(path)
            yield todo

    def _datetime_from_db(self, dt) -> datetime | None:
        if dt:
            return datetime.fromtimestamp(dt, LOCAL_TIMEZONE)
        return None

    def _date_from_db(self, dt, is_date=False) -> date | None:
        """Deserialise a date (possible datetime)."""
        if not dt:
            return dt

        if is_date:
            return datetime.fromtimestamp(dt, LOCAL_TIMEZONE).date()
        else:
            return datetime.fromtimestamp(dt, LOCAL_TIMEZONE)

    def _categories_from_db(self, categories):
        if categories:
            return categories.split(",")

        return []

    def _todo_from_db(self, row: dict) -> Todo:
        todo = Todo()
        todo.id = row["id"]
        todo.uid = row["uid"]
        todo.summary = row["summary"]
        todo.due = self._date_from_db(row["due"], row["due_dt"])
        todo.start = self._date_from_db(row["start"], row["start_dt"])
        todo.categories = self._categories_from_db(row["categories"])
        todo.priority = row["priority"]
        todo.created_at = self._datetime_from_db(row["created_at"])
        todo.completed_at = self._datetime_from_db(row["completed_at"])
        todo.dtstamp = self._datetime_from_db(row["dtstamp"])
        todo.percent_complete = row["percent_complete"]
        todo.status = row["status"]
        todo.description = row["description"]
        todo.location = row["location"]

        logger.debug("todo.categories: %s\n", todo.categories)
        todo.sequence = row["sequence"]
        todo.last_modified = row["last_modified"]
        todo.list = self.lists_map[row["list_name"]]
        todo.filename = os.path.basename(row["path"])
        todo.rrule = row["rrule"]
        return todo

    def lists(self) -> Iterable[TodoList]:
        result = self._conn.execute("SELECT * FROM lists")
        for row in result:
            yield TodoList(
                name=row["name"],
                path=row["path"],
                colour=row["colour"],
            )

    @cached_property
    def lists_map(self) -> dict[str, TodoList]:
        return {list_.name: list_ for list_ in self.lists()}

    def expire_lists(self, paths: dict[str, int]) -> None:
        results = self._conn.execute("SELECT path, name, mtime from lists")
        for result in results:
            if result["path"] not in paths:
                self.delete_list(result["name"])
            else:
                mtime = paths.get(result["path"])
                if mtime and mtime > result["mtime"]:
                    self.delete_list(result["name"])

    def delete_list(self, name: str) -> None:
        self._conn.execute("DELETE FROM lists WHERE lists.name = ?", (name,))

    def todo(self, id: int, read_only=False) -> Todo:
        # XXX: DON'T USE READ_ONLY
        result = self._conn.execute(
            """
            SELECT todos.*, files.list_name, files.path,
              group_concat(category) AS categories
            FROM todos, files
            LEFT JOIN categories
            ON categories.todos_id = todos.id
            WHERE files.path = todos.file_path
              AND todos.id = ?
            GROUP BY uid
        """,
            (id,),
        ).fetchone()

        if not result:
            raise exceptions.NoSuchTodoError(id)

        if not read_only:
            count = self._conn.execute(
                """
                SELECT count(id) AS c
                  FROM files, todos
                 WHERE todos.file_path = files.path
                   AND path=?
            """,
                (result["path"],),
            ).fetchone()
            if count["c"] > 1:
                raise exceptions.ReadOnlyTodoError(result["path"])

        return self._todo_from_db(result)

    def expire_files(self, paths_to_mtime: dict[str, int]) -> None:
        """Remove stale cache entries based on the given fresh data."""
        result = self._conn.execute("SELECT path, mtime FROM files")
        for row in result:
            path, mtime = row["path"], row["mtime"]
            if paths_to_mtime.get(path, None) != mtime:
                self.expire_file(path)

    def expire_file(self, path: str) -> None:
        self._conn.execute("DELETE FROM files WHERE path = ?", (path,))


class TodoList:
    def __init__(self, name: str, path: str, colour: str | None = None):
        self.path = path
        self.name = name
        self.colour = colour

    @staticmethod
    def colour_for_path(path: str) -> str | None:
        try:
            with open(os.path.join(path, "color")) as f:
                return f.read().strip()
        except OSError:
            logger.debug("No colour for list %s", path)

        return None

    @staticmethod
    def name_for_path(path: str) -> str:
        try:
            with open(os.path.join(path, "displayname")) as f:
                return f.read().strip()
        except OSError:
            return split(normpath(path))[1]

    @staticmethod
    def mtime_for_path(path: str) -> int:
        colour_file = os.path.join(path, "color")
        display_file = os.path.join(path, "displayname")

        mtimes = []
        if os.path.exists(colour_file):
            mtimes.append(_getmtime(colour_file))
        if os.path.exists(display_file):
            mtimes.append(_getmtime(display_file))

        if mtimes:
            return max(mtimes)
        else:
            return 0

    def __eq__(self, other) -> bool:
        if isinstance(other, TodoList):
            return self.name == other.name
        return object.__eq__(self, other)

    def __str__(self) -> str:
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

    def update_cache(self) -> None:
        paths = {path: TodoList.mtime_for_path(path) for path in self.paths}
        self.cache.expire_lists(paths)

        paths_to_mtime = {}
        paths_to_list_name = {}

        for path in self.paths:
            list_name = self.cache.add_list(
                TodoList.name_for_path(path),
                path,
                TodoList.colour_for_path(path),
                paths[path],
            )
            for entry in os.listdir(path):
                if not entry.endswith(".ics"):
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
            except exceptions.AlreadyExistsError:
                logger.debug("File already in cache: %s", entry_path)
                continue

            try:
                with open(entry_path, "rb") as f:
                    cal = icalendar.Calendar.from_ical(f.read())
                    for component in cal.walk("VTODO"):
                        self.cache.add_vtodo(component, entry_path)
            except Exception:
                logger.exception("Failed to read entry %s.", entry_path)

        self.cache.save_to_disk()

    def todos(self, **kwargs) -> Iterable[Todo]:
        return self.cache.todos(**kwargs)

    def todo(self, id: int, **kwargs) -> Todo:
        return self.cache.todo(id, **kwargs)

    def lists(self) -> Iterable[TodoList]:
        return self.cache.lists()

    def move(self, todo: Todo, new_list: TodoList, from_list: TodoList) -> None:
        orig_path = os.path.join(from_list.path, todo.filename)
        dest_path = os.path.join(new_list.path, todo.filename)

        os.rename(orig_path, dest_path)

    def delete(self, todo: Todo) -> None:
        if not todo.list:
            raise ValueError("Cannot delete Todo without a list.")

        path = os.path.join(todo.list.path, todo.filename)
        os.remove(path)

    def flush(self) -> Iterable[Todo]:
        for todo in self.todos(status=["ANY"]):
            if todo.is_completed:
                yield todo
                self.delete(todo)

        self.cache.clear()
        self.cache = None

    def save(self, todo: Todo) -> None:
        if not todo.list:
            raise ValueError("Cannot save Todo without a list.")

        for related in todo.related:
            self.save(related)

        todo.sequence += 1
        todo.last_modified = datetime.now(LOCAL_TIMEZONE)

        vtodo = VtodoWriter(todo).write()

        self.cache.expire_file(todo.path)
        mtime = _getmtime(todo.path)

        self.cache.add_file(todo.list.name, todo.path, mtime)
        todo.id = self.cache.add_vtodo(vtodo, todo.path, todo.id)
        self.cache.save_to_disk()


def _getmtime(path: str) -> int:
    return os.stat(path).st_mtime_ns
