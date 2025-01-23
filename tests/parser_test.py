from compiler.parser import parse
from compiler.tokenizer import tokenize
import compiler.ast as ast


def test_parser() -> None:
    assert parse(tokenize("3 + 5")) == ast.BinaryOp(
        ast.Literal(3),
        "+",
        ast.Literal(5)
    )
    
    assert parse(tokenize("a + 5")) == ast.BinaryOp(
        ast.Identifier('a'),
        "+",
        ast.Literal(5)
    )
    
    assert parse(tokenize("a + b")) == ast.BinaryOp(
        ast.Identifier('a'),
        "+",
        ast.Identifier('b')
    )