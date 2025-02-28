from dataclasses import dataclass

@dataclass
class Location:
    file: str
    line: int
    column: int
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Location):
            return NotImplemented
        if isinstance(value, DummyLocation):
            return True
        return (self.file == value.file and self.line == value.line and self.column == value.column)
    
class DummyLocation(Location):
    def __init__(self) -> None:
        self.file = 'dummy'
        self.line = -1
        self.column = -1
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Location):
            return NotImplemented
        return True

@dataclass
class Token:
    text: str
    type: str
    location: Location