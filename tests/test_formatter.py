from datetime import datetime, timedelta
from random import randrange
from todoman import ui

DATE_FORMAT = "%d-%m-%y"

def test_format_date():
    """
    Tests the format_date function in todoman.ui.TodoFormatter
    """
    formatter = ui.TodoFormatter(DATE_FORMAT)
    today = datetime.now().date()
    tomorrow = today + timedelta(days = 1)
    any_day = today + datetime.timedelta(days = random.randrange(2))

    str_format = lambda x: x.rjust((formatter.date_width), " ")

    assert formatter.format_date(today) == str_format("Today")
    assert formatter.format_date(tomorrow) == str_format("Tomorrow")
    assert formatter.format_date(any_day) == any_day.strftime(DATE_FORMAT)