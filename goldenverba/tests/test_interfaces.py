import pytest
from goldenverba.components.interfaces import SomeInterface

class TestSomeInterface:
    def test_interface_method(self):
        interface = SomeInterface()
        result = interface.some_method()
        assert result == "expected result"
