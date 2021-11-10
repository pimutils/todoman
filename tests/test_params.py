import hypothesis.strategies as st
import click
import pytest
from hypothesis import given

from todoman.cli import AppContext
from todoman.cli import Before
from todoman.cli import Priority
from todoman.cli import Status
from todoman.formatters import DefaultFormatter
from todoman.model import Todo


@pytest.fixture
def app_ctx():
    ctx = AppContext()
    ctx.formatter_class = DefaultFormatter
    ctx.config = {
        "date_format": "%x",
        "dt_separator": " ",
        "time_format": "%X",
    }

    return ctx


def test_priority(app_ctx):
    priority = Priority(app_ctx)

    assert priority.convert("none", None, None) == 0
    assert priority.convert("low", None, None) == 9
    assert priority.convert("medium", None, None) == 5
    assert priority.convert("high", None, None) == 4


def test_start_date(app_ctx):
    before_after = Before(app_ctx)

    assert before_after.convert("after", None, None) is False


def test_status_validation(app_ctx):
    status = Status(app_ctx)

    @given(
        statuses=st.lists(
            st.sampled_from(Todo.VALID_STATUSES + ("ANY",)),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    def run_test(statuses):
        validated = status.convert(",".join(statuses), None, None)

        if "ANY" in statuses:
            assert len(validated) == 4
        else:
            assert len(validated) == len(statuses)

        for convertd_status in validated:
            assert convertd_status in Todo.VALID_STATUSES

    run_test()


def test_bad_status_validation(app_ctx):
    status = Status(app_ctx)

    with pytest.raises(click.BadParameter):
        status.convert("INVALID", None, None)

    with pytest.raises(click.BadParameter):
        status.convert("IN-PROGRESS", None, None)
