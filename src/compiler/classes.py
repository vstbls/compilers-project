from dataclasses import dataclass
from typing import Self

@dataclass
class Location:
    file: str
    line: int
    column: int
    placeholder: bool = False
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Location):
            return NotImplemented
        if self.placeholder:
            return True
        return (self.file == value.file) and (self.line == value.line) and (self.column == value.column) 

@dataclass
class Token:
    text: str
    type: str
    source: Location