from typing import Literal

from pydantic import BaseModel


class InputConfig(BaseModel):
    type: Literal["number", "text", "dropdown", "password", "bool", "multi"]
    value: int | str | bool
    description: str
    values: list[str]
