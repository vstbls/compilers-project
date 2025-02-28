from dataclasses import dataclass, field
from compiler.classes import Location, DummyLocation
from compiler.types import Type, Unit


@dataclass
class Expression:
    location: Location = field(default_factory=lambda: DummyLocation(), init=False)
    type: Type = field(kw_only=True, default_factory=lambda: Unit(), compare=False)

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