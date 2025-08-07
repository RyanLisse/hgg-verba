from goldenverba.components.types import InputConfig


def test_input_config():
    # Test text input config
    text_config = InputConfig(
        type="text", value="test", description="A test input", values=[]
    )
    assert text_config.type == "text"
    assert text_config.value == "test"
    assert text_config.description == "A test input"
    assert text_config.values == []

    # Test number input config
    number_config = InputConfig(
        type="number", value=42, description="A number input", values=[]
    )
    assert number_config.type == "number"
    assert number_config.value == 42
