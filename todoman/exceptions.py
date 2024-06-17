from __future__ import annotations

from abc import ABC


class TodomanError(Exception, ABC):
    """
    Base class for all our exceptions.

    Should not be raised directly.
    """

    EXIT_CODE: int


class NoSuchTodoError(TodomanError):
    EXIT_CODE = 20

    def __str__(self) -> str:
        return f"No todo with id {self.args[0]}."


class ReadOnlyTodoError(TodomanError):
    EXIT_CODE = 21

    def __str__(self) -> str:
        return (
            "Todo is in read-only mode because there are multiple todos "
            f"in {self.args[0]}."
        )


class NoListsFoundError(TodomanError):
    EXIT_CODE = 22

    def __str__(self) -> str:
        return (
            f"No lists found matching {self.args[0]}, create a "
            "directory for a new list."
        )


class AlreadyExistsError(TodomanError):
    """
    Raised when two objects have a same identity.

    This can ocurrs when two lists have the same name, or when two Todos have
    the same path.
    """

    EXIT_CODE = 23

    def __str__(self) -> str:
        return "More than one {} has the same identity: {}.".format(*self.args)
