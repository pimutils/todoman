import logging

import urwid

from .model import Todo
from .ui import EditState, TodoEditor


logging.basicConfig()
logger = logging.getLogger()


class TodomanItem(urwid.CheckBox):
    '''
    Class to contain a single todo item in a ListBox.
    '''

    def __init__(self, todo, database, labelmaker):
        '''
        Create a TodomanItem instance based on the filename and the associated
        Database that was provided. By providing the filename instead of the
        Todo itself, we do not need to check if the provided todo is indeed in
        in the given Database. The labelmaker is a function that turns a given
        TodomanItem (i.e. self) into a string representation that is suitable
        for its context.

        (TodomanItem, str, Database, function) -> None
        '''
        self.database = database
        if todo:
            self.todo = todo
        else:
            self.todo = Todo()  # A new todo is created
            self.filename = self.todo.filename
        # If the done status changes, save to database
        urwid.connect_signal(self, 'change', self.save)
        super().__init__(labelmaker(self), self.is_completed)

    @property
    def is_completed(self):
        '''
        Returns True iff the TodomanItem refers to a completed Todo.

        (TodomanItem) -> bool
        '''
        return self.todo.is_completed

    @is_completed.setter
    def is_completed(self, status):
        '''
        Set the given status as the status of the Todo to which the TodomanItem
        refers.

        (TodomanItem, bool) -> None
        '''
        self.todo.is_completed = status
        self.save()

    def save(self, *args):
        '''
        Save the current state of the TodomanItem and the Todo to which it
        refers in the associated Database.

        (TodomanItem, *args) -> None
        '''
        # Todoman and Urwid have inverted notions of state. According to Urwid,
        # the state of something that is done is 'False'.
        if self.get_state():
            self.todo.is_completed = False
        else:
            self.todo.is_completed = True
        self.database.save(self.todo)

    @property
    def has_priority(self):
        '''
        Returns True iff the TodomanItem refers to a Todo with a priority that
        is set (i.e. not None and above zero).

        (self) -> bool
        '''
        return self.todo.priority not in [None, 0]


class TodomanPage(urwid.Frame):
    '''
    Abstract class. Inherit from this class and an appropriate Urwid Widget
    class to create a new page type.
    '''

    def __init__(self, parent, callback):
        '''
        Create an instance of TodomanPage. The parent is the TodomanInteractive
        instance in which the page was created.

        Any subclass that calls this method should first set self.body to
        the box widget that should be the body of the Frame.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying TodomanPage.
        It is usually a method of the underlying TodomanPage. If callback is
        None, use the default.

        (TodomanPage, TodomanInteractive, function) -> None
        '''
        self.parent = parent
        if callback:
            self.callback = callback
        header = urwid.AttrMap(urwid.Text(" Todoman"), "statusbar")
        statusbar = urwid.AttrMap(urwid.Text(""), "statusbar")
        inputline = urwid.Edit()
        footer = urwid.Pile([statusbar, inputline])
        super().__init__(self.body, header, footer)

    def open_page(self, page_to_open):
        '''
        Open a page over the existing stack of pages. page_to_open is the
        TodomanPage object to display.

        (TodomanPage, TodomanPage) -> None
        '''
        self.parent._open_page(page_to_open)

    @property
    def statusbar(self):
        '''
        Returns the current contents of the statusbar of the Todomanpage.

        (TodomanPage) -> str
        '''
        return self.footer.contents[0].original_widget.text

    @statusbar.setter
    def statusbar(self, text):
        '''
        Sets the given text as the current text in the statusbar of the
        TodomanPage.

        (self, str) -> None
        '''
        self.footer.contents
        self.footer.contents[0][0].original_widget.set_text(text)

    def callback(self, **kwargs):
        '''
        A default callback function to use when closing the previous page.
        This callback function handles several keywords that are generic to
        all callbacks. If a certain keyword is not set, the method does
        nothing with it.

        This callback function supports the following keywords:

        statusbar (str): A text to set as the statusbar message

        (TodomanPage, **kwargs) -> None
        '''
        for key, value in kwargs.items():
            if key == 'statusbar':
                self.statusbar = value
        self.reload()

    def reload(self):
        '''
        Dummy method. TodomanPage subclasses that need a reload should
        implement one under this name.

        (TodomanPage) -> None
        '''
        return None


class TodomanItemListPage(TodomanPage):
    '''
    Class to contain a ListBox filled with todo items, based on a given
    Database.
    '''

    def __init__(self, parent, callback, database):
        '''
        Create an instance of TodomanItemListPage. The parent is the
        TodomanInteractive instance in which the page was created.
        The database is the Database from which to display items.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying TodomanPage.
        It is usually a method of the underlying TodomanPage.

        (TodomanItemListPage, TodomanInteractive, function, Database) -> None
        '''
        self.parent = parent
        self.database = database
        # By default, we hide the completed items
        self.done_is_hidden = True
        items = self.items_to_display()
        self.body = urwid.ListBox(urwid.SimpleFocusListWalker(items))
        super().__init__(parent, callback)

    def items_to_display(self):
        '''
        Create a list of TodomanItems to display, based on the associated
        Database and the current done_is_hidden setting.

        (TodomanItemListPage) -> [TodomanItem]
        '''
        items = []
        for t in self.database.todos():
            todo = TodomanItem(t, self.database, self.generate_label)
            if not self.done_is_hidden or not todo.is_completed:
                items.append(todo)
        items.sort(key=lambda item: item.label.lower())
        return items

    def callback_move_to(self, **kwargs):
        '''
        Move the TodomanItem in focus to Database database.

        (TodomanItemListPage, Database) -> None
        '''
        for key, value in kwargs.items():
            if key == "database" and value != self.database:
                value.save(self.body.focus.todo)
                self.database.delete(self.body.focus.todo)
                self.body.body.remove(self.body.focus)
                self.statusbar = "Item moved to {0}.".format(value.name)

    def move_database_chooser(self):
        '''
        Open a TodomanDatabasesPage from which to choose the destination of the
        move operation for the selected item.

        (TodomanItemListPage) -> None
        '''
        new_page = TodomanDatabasesPage(self.parent, self.callback_move_to)
        self.open_page(new_page)

    def callback_copy_to(self, **kwargs):
        '''
        Copy the TodomanItem in focus to Database database.

        (TodomanItemListPage, Database) -> None
        '''
        for key, value in kwargs.items():
            if key == "database" and value != self.database:
                value.save(self.body.focus.todo)
                self.statusbar = "Item copied to {0}.".format(value.name)

    def copy_database_chooser(self):
        '''
        Open a TodomanDatabasesPage from which to choose the destination of the
        copy operation for the selected item.

        (TodomanItemListPage) -> None
        '''
        new_page = TodomanDatabasesPage(self.parent, self.callback_copy_to)
        self.open_page(new_page)

    def delete(self, item=None):
        '''
        Delete the TodomanItem item from its database. By default, delete the
        item in focus.

        (TodomanItemListPage, TodomanItem) -> None
        '''
        if item is None:
            item = self.body.focus
        item.database.delete(item.todo)
        self.body.body.remove(item)

    def generate_label(self, item):
        '''
        Return a label for a given TodomanItem for display in the
        TodomanItemListPage listing.

        (TodomanItemListPage, TodomanItem) -> str
        '''
        return "{0} {1}".format(
            '!' if item.has_priority else ' ', item.todo.summary
        )

    def keypress(self, size, key):
        '''
        Make the different commands in the TodomanItemListPage view work.

        (TodomanItemListPage, int(?), str) -> str
        '''
        if key == 'l':
            self.list_chooser()
            return None
        if key == 'm':
            self.move_database_chooser()
            return None
        if key == 'c':
            self.copy_database_chooser()
            return None
        if key == 'd':
            self.delete()
            return None
        if key == 'D':
            self.delete_all_done()
            return None
        if key == 'esc':
            self.parent.close_page(self)
            return None
        if key == 'h':
            self.toggle_hide_completed_items()
            return None
        if key == 'e':
            self.item_details()
            return None
        if key == 'n':
            self.new_item()
            return None
        if key == 'j':
            return super().keypress(size, 'down')
        if key == 'k':
            return super().keypress(size, 'up')
        return super().keypress(size, key)

    def list_chooser(self):
        '''
        Open a TodomanDatabasesPage from which to choose the
        TodomanItemListPage to display.

        (TodomanItemListPage) -> None
        '''
        new_page = TodomanDatabasesPage(
            self.parent,
            self.callback_open_other_database,
        )
        self.open_page(new_page)

    def callback_open_other_database(self, **kwargs):
        '''
        Callback function for the ListChooser option. Opens the Database that
        the user selected in the TodomanDatabasesPage, and passes all arguments
        to the default callback for further processing. The new TodomanPage
        will be opened over the old one.

        This callback function handles the following keywords, in addition
        to the keywords TodomanPage.callback handles:

        * database (Database): the Database to display in the new page.

        (TodomanItemListPage, **kwargs) -> None
        '''
        for key, value in kwargs.items():
            if key == "database" and value != self.database:
                new_page = TodomanItemListPage(self.parent, None, value)
                self.open_page(new_page)

    def item_details(self):
        '''
        Open a TodomanItemDetailsPage in which the user can edit the selected
        TodomanItem.

        (TodomanItemListPage) -> None
        '''
        new_page = TodomanItemDetailsPage(
            self.parent,
            self.callback,
            self.body.focus,
        )
        self.open_page(new_page)

    def new_item(self):
        '''
        Create a new TodomanItem and open a TodomanItemDetailsPage in which
        the user can edit the new item.

        (TodomanItemListPage) -> None
        '''
        item = TodomanItem(None, self.database, self.generate_label)
        new_page = TodomanItemDetailsPage(self.parent, self.callback, item)
        self.open_page(new_page)

    def toggle_hide_completed_items(self):
        '''
        Toggle whether completed items are still displayed in the TodomanPage.

        (TodomanItemListPage) -> None
        '''
        self.done_is_hidden = not self.done_is_hidden
        self.reload()

    def delete_all_done(self):
        '''
        Delete all TodomanItems for which the associated Todos are completed.

        (TodomanItemListPage) -> None
        '''
        to_delete = []
        for item in self.body.body:
            if item.is_completed:
                to_delete.append(item)
        for item in to_delete:
            self.delete(item)

    def reload(self):
        '''
        Reload all TodomanItems in the ListBox from the underlying Database.

        (TodomanItemListPage) -> None
        '''
        items = self.items_to_display()
        self.body = urwid.ListBox(urwid.SimpleFocusListWalker(items))
        super().__init__(self.parent, self.callback)


class TodomanItemDetailsPage(TodomanPage):
    '''
    Class to contain a TodoEditor filled with all the fields that a given
    TodomanItem contains. Allows the user to view and edit all attributes of
    the TodomanItem.
    '''

    def __init__(self, parent, callback, item):
        '''
        Create an instance of TodomanItemDetailsPage. The parent is the
        TodomanInteractive instance in which the page was created.
        Item is the TodomanItem of which the details will be shown and
        edited.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying TodomanPage.
        It is usually a method of the underlying TodomanPage.

        (TodomanItemDetailsPage, TodomanInteractive, function, TodomanItem)
            -> None
        '''
        self.parent = parent
        self.item = item
        self.editor = TodoEditor(
            item.todo,
            self.parent.databases,
            self.parent.formatter,
        )
        self.body = self.editor._ui
        button = self.body.body.contents[-1].contents[0][0]
        # Do not use regular callback, as that exits the MainLoop
        urwid.disconnect_signal(button, 'click', self.editor._save)
        urwid.connect_signal(button, 'click', self.close_page, True)
        # Remove helper text, as the commands do not work the same way
        self.body.body.contents[-1].contents[1][0].set_text("")
        super().__init__(parent, callback)

    def close_page(self, dummy, should_save):
        '''
        Callback for closing the TodomanItemDetailsPage. Will attempt to save
        all associated data if shouldSave is True. Will discard all changes
        otherwise.

        (TodomanItemDetailsPage, Button, bool) -> None
        '''
        if should_save:
            try:
                self.editor._save_inner()
                self.item.save()
            except Exception as e:
                self.message(('error', str(e)))
            else:
                self.editor.saved = EditState.saved
                self.parent.close_page(self, statusbar="Item saved.")
        else:
            self.parent.close_page(self, statusbar="Item not saved.")

    def keypress(self, size, key):
        '''
        Make the different commands in the TodomanItemDetailsPage view work.

        (TodomanItemDetailsPage, int(?), str) -> str
        '''
        if key == 'esc':
            self.close_page(None, False)
            return None
        return super().keypress(size, key)


class TodomanDatabasesPage(TodomanPage):
    '''
    Class to contain a ListBox filled with all available Databases. The user
    can choose a Database from the list, after which the TodomanDatabasesPage
    closes again and the chosen Database is passed back to the callback.
    '''

    def __init__(self, parent, callback):
        '''
        Create a TodomanDatabasesPage instance.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying TodomanPage.
        It is usually a method of the underlying TodomanPage.

        (TodomanDatabasesPage, TodomanInteractive, function) -> None
        '''
        self.parent = parent
        buttons = []
        for database in parent.databases:
            button = urwid.Button("")
            urwid.connect_signal(button, 'click', self.close_page, database)
            button._w = urwid.AttrMap(urwid.SelectableIcon(
                        ["> ", database.name], 2), None, 'selected')
            buttons.append(button)
        self.body = urwid.ListBox(urwid.SimpleFocusListWalker(buttons))
        super().__init__(parent, callback)

    def close_page(self, button, database):
        '''
        Close the current page, returning the selected database to the
        underlying page.

        (TodomanDatabasesPage, Button, Database) -> None
        '''
        self.parent.close_page(self, database=database)

    def keypress(self, size, key):
        '''
        Make the different commands in the TodomanDatabasesPage view work.

        (TodomanDatabasesPage, int(?), str) -> str
        '''
        if key == 'esc':
            self.parent.close_page(self)
            return None
        if key == 'j':
            return super().keypress(size, 'down')
        if key == 'k':
            return super().keypress(size, 'up')
        return super().keypress(size, key)


class TodomanInteractive(object):
    '''
    Class to run the interactive, curses-based interface to Todoman.
    '''

    palette = [
        ('statusbar', 'light gray', 'dark blue'),
        ('reversed', 'standout', ''),
        ('error', 'light red', '')
    ]

    def __init__(self, databases, formatter):
        '''
        Create a TodomanInteractive instance based on the Database objects that
        the regular Todoman cli module passes.

        (TodomanInteractive, [Database], TodoFormatter) -> None
        '''
        self.databases = databases
        # self.databases.sort(key = lambda db: db.name)
        self.formatter = formatter
        top = urwid.Filler(urwid.Text("Press q to exit"))
        self.loop = urwid.MainLoop(
            top,
            self.palette,
            unhandled_input=self.unhandled_input,
        )
        first_page = TodomanItemListPage(self, None, self.databases)
        self.pageCounter = 0
        self._open_page(first_page)

        self.loop.run()

    def unhandled_input(self, key):
        '''
        Handles all the key presses that are application-wide.

        (TodomanInteractive, str) -> None
        '''
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    def _open_page(self, page_to_open):
        '''
        Open a page over the existing stack of pages. page_to_open is the
        TodomanPage object to display.

        (TodomanInteractive, TodomanPage) -> None
        '''
        self.loop.widget = urwid.Overlay(
            page_to_open,
            self.loop.widget,
            'left', ('relative', 100),
            'middle', ('relative', 100))
        self.pageCounter += 1

    def close_page(self, page, **kwargs):
        '''
        Close the topmost open page, passing the given information to the
        TodomanPage below via the callback that was provided when opening
        the TodomanPage.

        Usually called from the page to be closed.

        (TodomanInteractive, TodomanPage, **kwargs) -> None
        '''
        if self.pageCounter <= 1:
            raise urwid.ExitMainLoop()
        else:
            self.loop.widget = self.loop.widget.contents[0][0]
            self.pageCounter -= 1
        if page.callback:
            page.callback(**kwargs)
