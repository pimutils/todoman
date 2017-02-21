from datetime import datetime, timedelta
from random import randrange

from todoman import ui

DATE_FORMAT = "%d-%m-%y"


def test_format_date():
    """
    Tests the format_date function in todoman.ui.TodoFormatter
    """
    formatter = ui.TodoFormatter(DATE_FORMAT)
    date_width = formatter.date_width
    today = datetime.now()
    tomorrow = today + timedelta(days = 1)
    any_day = today + timedelta(days = randrange(2, 8))

    assert formatter.format_date(today) == "Today".rjust(date_width)
    assert formatter.format_date(tomorrow) == "Tomorrow".rjust(date_width)
    assert formatter.format_date(any_day) == any_day.strftime(DATE_FORMAT)
