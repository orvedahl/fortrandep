import os
import pytest

@pytest.fixture
def filesdir():
    return os.path.dirname(os.path.abspath(__file__))

