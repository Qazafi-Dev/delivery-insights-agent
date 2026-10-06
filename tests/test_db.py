import pytest

from delivery_insights_agent.db import validate_query


def test_allows_select():
    assert validate_query("SELECT 1;") == "SELECT 1"


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET tip = 0",
        "SELECT 1; DROP TABLE orders",
    ],
)
def test_blocks_unsafe_queries(query):
    with pytest.raises(ValueError):
        validate_query(query)
