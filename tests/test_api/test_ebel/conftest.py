"""Init API unit tests."""

import json
import pytest

from typing import Union

from ebel.web.app import application


@pytest.fixture(scope="module")
def client():
    with application.app.test_client() as client:
        yield client


def format_response_data(response) -> Union[dict, list]:
    """Used to query to test client and retrieve the data."""
    assert response.status_code == 200
    return json.loads(response.data)
