from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Any
from compiler.classes import Location, DummyLocation
from compiler.types import Type, Unit, FnType


@dataclass
class Node:
    location: Location = field(kw_only=True, default_factory=lambda: DummyLocation(), compare=False)
    type: Type = field(kw_only=True, default_factory=lambda: Unit(), compare=False)
    
    def __str__(self) -> str:
        def format_value(v: Any) -> str:
            if isinstance(v, list):
                return f'[{", ".join(format_value(e) for e in v)}]'
            else:
                return str(v)
        args = ', '.join(
            format_value(getattr(self, field.name))
            for field in fields(self)
            if field.name != 'location'
        )
        return f'{type(self).__name__}(\n{args}\n)'

@dataclass
class Module(Node):
    defs: list[Definition]
    expr: Expression | None

@dataclass
class Definition(Node):
    name: str
    params: list[Identifier]
    block: Block
    type: FnType = field(kw_only=True, default_factory=lambda: FnType([], Unit()), compare=False)

@dataclass
class Expression(Node):
    pass

@dataclass
class Literal(Expression):
    value: int | bool | None

@dataclass
class Identifier(Expression):
    name: str
    
@dataclass
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression

@dataclass
class UnaryOp(Expression):
    op: str
    param: Expression

@dataclass
class If(Expression):
    condition: Expression
    true_branch: Expression
    false_branch: None | Expression = None

@dataclass
class Function(Expression):
    id: Identifier
    args: list[Expression] = field(default_factory=list)

@dataclass
class Block(Expression):
    exprs: list[Expression]
    res: Expression | None = None

@dataclass
class While(Expression):
    condition: Expression
    expr: Expression

@dataclass
class Var(Expression):
    id: Identifier
    expr: Expression
    typed: bool = False

@dataclass
class Break(Expression):
    pass

@dataclass
class Continue(Expression):
    pass

@dataclass
class Return(Expression):
    expr: Expression | None