import logging

import urwid

from .model import Todo
from .ui import EditState, TodoEditor


logging.basicConfig()
logger = logging.getLogger()


class Item(urwid.CheckBox):
    '''
    Class to contain a single todo item in a ListBox.
    '''

    def __init__(self, todo, database, labelmaker):
        '''
        Create a Item instance based on a todo and the associated
        Database that was provided.

        :param todoman.model.Todo todo: The todo this entry will represent.
        :param todoman.model.Database: The database from which persists tihs
            todo.
        :param func labelmake: A function that will create the string
            representation for this item.
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
        return self.todo.is_completed

    @is_completed.setter
    def is_completed(self, status):
        self.todo.is_completed = status
        self.save()

    def save(self, *args):
        '''
        Save the current state of the Item and the Todo to which it
        refers in the associated Database.

        (Item, *args) -> None
        '''
        # Todoman and Urwid have inverted notions of state. According to Urwid,
        # the state of something that is done is 'False'.
        self.todo.is_completed = not self.get_state()
        self.database.save(self.todo)

    @property
    def has_priority(self):
        '''
        Returns True iff the Item refers to a Todo with a priority that
        is set (i.e. not None and above zero).

        (self) -> bool
        '''
        return self.todo.priority not in (None, 0)


class Page(urwid.Frame):
    '''
    Abstract class. Inherit from this class and an appropriate Urwid Widget
    class to create a new page type.
    '''

    def __init__(self, parent, callback):
        '''
        Create an instance of Page. The parent is the Main
        instance in which the page was created.

        Any subclass that calls this method should first set self.body to
        the box widget that should be the body of the Frame.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying Page.
        It is usually a method of the underlying Page. If callback is
        None, use the default.

        (Page, Main, function) -> None
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
        Page object to display.

        (Page, Page) -> None
        '''
        self.parent._open_page(page_to_open)

    @property
    def statusbar(self):
        '''
        Returns the current contents of the statusbar of the Todomanpage.

        (Page) -> str
        '''
        return self.footer.contents[0].original_widget.text

    @statusbar.setter
    def statusbar(self, text):
        '''
        Sets the given text as the current text in the statusbar of the
        Page.

        (self, str) -> None
        '''
        self.footer.contents
        self.footer.contents[0][0].original_widget.set_text(text)

    def callback(self, statusbar):
        '''
        A default callback function to use when closing the previous page.
        This callback function handles several keywords that are generic to
        all callbacks. If a certain keyword is not set, the method does
        nothing with it.

        This callback function supports the following keywords:

        :param statusbar: A text to set as the statusbar message
        '''
        self.statusbar = statusbar
        self.reload()

    def reload(self):
        '''
        Dummy method. Page subclasses that need a reload should
        implement one under this name.

        (Page) -> None
        '''
        return None


class ItemListPage(Page):
    '''
    Class to contain a ListBox filled with todo items, based on a given
    Database.
    '''

    def __init__(self, parent, callback, database):
        '''
        Create an instance of ItemListPage. The parent is the
        Main instance in which the page was created.
        The database is the Database from which to display items.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying Page.
        It is usually a method of the underlying Page.

        (ItemListPage, Main, function, Database) -> None
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
        Create a list of Items to display, based on the associated
        Database and the current done_is_hidden setting.

        (ItemListPage) -> [Item]
        '''
        items = []
        for t in self.database.todos():
            todo = Item(t, self.database, self.generate_label)
            if not self.done_is_hidden or not todo.is_completed:
                items.append(todo)
        items.sort(key=lambda item: item.label.lower())
        return items

    def callback_move_to(self, database):
        '''
        Move the Item in focus to Database database.
        '''
        if database != self.database:
            database.save(self.body.focus.todo)
            self.database.delete(self.body.focus.todo)
            self.body.body.remove(self.body.focus)
            self.statusbar = "Item moved to {0}.".format(database.name)

    def move_database_chooser(self):
        '''
        Open a ListsPage from which to choose the destination of the
        move operation for the selected item.
        '''
        new_page = ListsPage(self.parent, self.callback_move_to)
        self.open_page(new_page)

    def callback_copy_to(self, database):
        '''
        Copy the Item in focus to Database database.

        (ItemListPage, Database) -> None
        '''
        if database != self.database:
            database.save(self.body.focus.todo)
            self.statusbar = "Item copied to {0}.".format(database.name)

    def copy_database_chooser(self):
        '''
        Open a ListsPage from which to choose the destination of the
        copy operation for the selected item.
        '''
        new_page = ListsPage(self.parent, self.callback_copy_to)
        self.open_page(new_page)

    def delete(self, item=None):
        '''
        Delete the Item item from its database. By default, delete the
        item in focus.

        :type item: Item
        '''
        if item is None:
            item = self.body.focus
        item.database.delete(item.todo)
        self.body.body.remove(item)

    def generate_label(self, item):
        '''
        Return a label for a given Item for display in the
        ItemListPage listing.

        (ItemListPage, Item) -> str
        '''
        return "{0} {1}".format(
            '!' if item.has_priority else ' ', item.todo.summary
        )

    def keypress(self, size, key):
        '''
        Make the different commands in the ItemListPage view work.

        (ItemListPage, int(?), str) -> str
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
        Open a ListsPage from which to choose the
        ItemListPage to display.

        (ItemListPage) -> None
        '''
        new_page = ListsPage(
            self.parent,
            self.callback_open_other_database,
        )
        self.open_page(new_page)

    def callback_open_other_database(self, database):
        '''
        Callback function for the ListChooser option. Opens the Database that
        the user selected in the ListsPage, and passes all arguments
        to the default callback for further processing. The new Page
        will be opened over the old one.

        This callback function handles the following keywords, in addition
        to the keywords Page.callback handles:

        :param database: the Database to display in the new page.
        :type database: Database
        '''
        if database != self.database:
            new_page = ItemListPage(self.parent, None, database)
            self.open_page(new_page)

    def item_details(self):
        '''
        Open a ItemDetailsPage in which the user can edit the selected
        Item.

        (ItemListPage) -> None
        '''
        new_page = ItemDetailsPage(
            self.parent,
            self.callback,
            self.body.focus,
        )
        self.open_page(new_page)

    def new_item(self):
        '''
        Create a new Item and open a ItemDetailsPage in which
        the user can edit the new item.

        (ItemListPage) -> None
        '''
        item = Item(None, self.database, self.generate_label)
        new_page = ItemDetailsPage(self.parent, self.callback, item)
        self.open_page(new_page)

    def toggle_hide_completed_items(self):
        '''
        Toggle whether completed items are still displayed in the Page.

        (ItemListPage) -> None
        '''
        self.done_is_hidden = not self.done_is_hidden
        self.reload()

    def delete_all_done(self):
        '''
        Delete all Items for which the associated Todos are completed.

        (ItemListPage) -> None
        '''
        to_delete = []
        for item in self.body.body:
            if item.is_completed:
                to_delete.append(item)
        for item in to_delete:
            self.delete(item)

    def reload(self):
        '''
        Reload all Items in the ListBox from the underlying Database.

        (ItemListPage) -> None
        '''
        items = self.items_to_display()
        self.body = urwid.ListBox(urwid.SimpleFocusListWalker(items))
        super().__init__(self.parent, self.callback)


class ItemDetailsPage(Page):
    '''
    Class to contain a TodoEditor filled with all the fields that a given
    Item contains. Allows the user to view and edit all attributes of
    the Item.
    '''

    def __init__(self, parent, callback, item):
        '''
        Create an instance of ItemDetailsPage. The parent is the
        Main instance in which the page was created.
        Item is the Item of which the details will be shown and
        edited.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying Page.
        It is usually a method of the underlying Page.

        (ItemDetailsPage, Main, function, Item)
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
        Callback for closing the ItemDetailsPage. Will attempt to save
        all associated data if shouldSave is True. Will discard all changes
        otherwise.

        (ItemDetailsPage, Button, bool) -> None
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
        Make the different commands in the ItemDetailsPage view work.

        (ItemDetailsPage, int(?), str) -> str
        '''
        if key == 'esc':
            self.close_page(None, False)
            return None
        return super().keypress(size, key)


class ListsPage(Page):
    '''
    Class to contain a ListBox filled with all available Databases. The user
    can choose a Database from the list, after which the ListsPage
    closes again and the chosen Database is passed back to the callback.
    '''

    def __init__(self, parent, callback):
        '''
        Create a ListsPage instance.

        Callback is the function to call when the page is closed. This function
        is responsible for passing information to the underlying Page.
        It is usually a method of the underlying Page.

        (ListsPage, Main, function) -> None
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

        (ListsPage, Button, Database) -> None
        '''
        self.parent.close_page(self, database=database)

    def keypress(self, size, key):
        '''
        Make the different commands in the ListsPage view work.

        (ListsPage, int(?), str) -> str
        '''
        if key == 'esc':
            self.parent.close_page(self)
            return None
        if key == 'j':
            return super().keypress(size, 'down')
        if key == 'k':
            return super().keypress(size, 'up')
        return super().keypress(size, key)


class Main(object):
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
        Create a Main instance based on the Database objects that
        the regular Todoman cli module passes.

        :type databases: list[Database]
        :type formatter: TodoFormatter
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
        first_page = ItemListPage(self, None, self.databases)
        self.pageCounter = 0
        self._open_page(first_page)

        self.loop.run()

    def unhandled_input(self, key):
        '''
        Handles all the key presses that are application-wide.

        :type key: str
        '''
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    def _open_page(self, page_to_open):
        '''
        Open a page over the existing stack of pages. page_to_open is the
        Page object to display.

        :type page_to_open: Page
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
        Page below via the callback that was provided when opening
        the Page.

        Usually called from the page to be closed.

        :type page: Page
        '''
        if self.pageCounter <= 1:
            raise urwid.ExitMainLoop()
        else:
            self.loop.widget = self.loop.widget.contents[0][0]
            self.pageCounter -= 1
        if page.callback:
            page.callback(**kwargs)
