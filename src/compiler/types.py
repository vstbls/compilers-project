from dataclasses import dataclass

@dataclass
class Type():
    pass

@dataclass
class Int(Type):
    pass

@dataclass
class Bool(Type):
    pass

@dataclass
class Unit(Type):
    pass

@dataclass
class FnType(Type):
    params: list[Type]
    res: Type