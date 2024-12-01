import pytest
from goldenverba.components.types import SomeType


def test_some_type_initialization():
    instance = SomeType("value")
    assert instance.value == "value"
