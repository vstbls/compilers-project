from compiler.parser import parse
from compiler.tokenizer import tokenize
import compiler.ast as ast

def parse_string(s: str) -> ast.Expression: return parse(tokenize(s))

def assert_parse_fail(s: str) -> None:
    try:
        parse_string(s)
    except:
        return
    raise AssertionError(f"Parsing didn't fail with input {s}")

def test_addition_parsing() -> None:
    assert parse_string("3 +5+ 7") == ast.BinaryOp(
        ast.BinaryOp(
            ast.Literal(3),
            "+",
            ast.Literal(5)
        ),
        "+",
        ast.Literal(7)
    )

    assert_parse_fail("3++")
    
    # TEST FOR RIGHT-ASSOCIATIVE PARSING
    # assert parse_string("3 + 5 + 7")) == ast.BinaryOp(
    #     ast.Literal(3),
    #     "+",
    #     ast.BinaryOp(
    #         ast.Literal(5),
    #         "+",
    #         ast.Literal(7)
    #     )
    # )
    
    assert parse_string("a + 5") == ast.BinaryOp(
        ast.Identifier('a'),
        "+",
        ast.Literal(5)
    )
    
    assert parse_string("a + b") == ast.BinaryOp(
        ast.Identifier('a'),
        "+",
        ast.Identifier('b')
    )
    
def test_multiplication_parsing() -> None:
    assert parse_string("a / b") == ast.BinaryOp(
        ast.Identifier('a'),
        "/",
        ast.Identifier('b')
    )
    
    assert parse_string("3 *5   / 7") == ast.BinaryOp(
        ast.BinaryOp(
            ast.Literal(3),
            "*",
            ast.Literal(5)
        ),
        "/",
        ast.Literal(7)
    )
    
    assert parse_string("3 *5   - 7") == ast.BinaryOp(
        ast.BinaryOp(
            ast.Literal(3),
            "*",
            ast.Literal(5)
        ),
        "-",
        ast.Literal(7)
    )
    
    assert parse_string(" 3-3 *5   / 7") == ast.BinaryOp(
        ast.Literal(3),
        "-",
        ast.BinaryOp(
            ast.BinaryOp(
                ast.Literal(3),
                "*",
                ast.Literal(5)
            ),
            "/",
            ast.Literal(7)
        )
    )

def test_parenthesis_parsing() -> None:
    assert parse_string(" 3-((3 *5)   / 7)") == ast.BinaryOp(
        ast.Literal(3),
        "-",
        ast.BinaryOp(
            ast.BinaryOp(
                ast.Literal(3),
                "*",
                ast.Literal(5)
            ),
            "/",
            ast.Literal(7)
        )
    )
    
    assert parse_string("(3-2) / 7") == ast.BinaryOp(
        ast.BinaryOp(
            ast.Literal(3),
            '-',
            ast.Literal(2)
            ),
        '/',
        ast.Literal(value=7)
    )
    
    assert parse_string("(3-2)/ (7+5)") == ast.BinaryOp(
        left=ast.BinaryOp(
            left=ast.Literal(value=3),
            op='-',
            right=ast.Literal(value=2)
        ),
        op='/',
        right=ast.BinaryOp(
            left=ast.Literal(value=7),
            op='+',
            right=ast.Literal(value=5)
        )
    )