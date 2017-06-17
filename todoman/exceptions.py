class TodomanException(Exception):
    """
    Base class for all our exceptions.

    Should not be raised directly.
    """
    pass


class NoSuchTodo(TodomanException):
    EXIT_CODE = 20

    def __str__(self):
        return 'No todo with id {}.'.format(self.args[0])


class ReadOnlyTodo(TodomanException):
    EXIT_CODE = 21

    def __str__(self):
        return (
            'Todo is in read-only mode because there are multiple todos in {}.'
            .format(self.args[0])
        )


class NoListsFound(TodomanException):
    EXIT_CODE = 22

    def __str__(self):
        return (
            'No lists found matching {}, create a directory for a new list.'
            .format(self.args[0])
        )


class AlreadyExists(TodomanException):
    """
    Raised when two objects have a same identity.

    This can ocurrs when two lists have the same name, or when two Todos have
    the same path.
    """

    EXIT_CODE = 23

    def __str__(self):
        return 'More than one {} has the same identity: {}.'.format(*self.args)
