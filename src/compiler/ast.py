from dataclasses import dataclass


@dataclass
class Expression:
    pass

@dataclass
class Literal(Expression):
    value: int | bool

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
    false_branch: None | Expression

@dataclass
class Function(Expression):
    name: Identifier
    args: list[Expression]