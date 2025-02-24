from dataclasses import dataclass

@dataclass
class Type():
    pass

@dataclass
class Int(Type):
    def __str__(self) -> str:
        return 'Int'

@dataclass
class Bool(Type):
    def __str__(self) -> str:
        return 'Bool'

@dataclass
class Unit(Type):
    def __str__(self) -> str:
        return 'Unit'

@dataclass
class FnType(Type):
    params: list[Type]
    res: Type
    
    def __str__(self) -> str:
        return f'({", ".join(map(str, self.params))}) => {self.res}'