from compiler.parser import parse
from compiler.tokenizer import tokenize
import compiler.ast as ast
from compiler.ast import *
from compiler.types import *

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

    assert parse_string("1 + false") == ast.BinaryOp(
        Literal(1),
        "+",
        Literal(False)
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
        ast.UnaryOp(
            "()",
            ast.BinaryOp(
                ast.UnaryOp(
                    "()",
                    ast.BinaryOp(
                        ast.Literal(3),
                        "*",
                        ast.Literal(5)
                    ),
                ),
                "/",
                ast.Literal(7)
            )
        )
        
    )
    
    assert parse_string("(3-2) / 7") == ast.BinaryOp(
        ast.UnaryOp(
            "()",
            ast.BinaryOp(
                ast.Literal(3),
                '-',
                ast.Literal(2)
            ),
        ),
        '/',
        ast.Literal(value=7)
    )
    
    assert parse_string("(3-2)/ (7+5)") == ast.BinaryOp(
        ast.UnaryOp(
            "()",
            ast.BinaryOp(
                ast.Literal(value=3),
                '-',
                ast.Literal(value=2)
            )
        ),
        '/',
        ast.UnaryOp(
            "()",
            ast.BinaryOp(
                ast.Literal(value=7),
                '+',
                ast.Literal(value=5)
            )
        )
    )

def test_conditional_parsing() -> None:
    assert parse_string("if a then b else c") == If(
        condition=Identifier('a'),
        true_branch=Identifier('b'),
        false_branch=Identifier('c')
    )

    assert parse_string("if if a then b else c then a + 2 else (a or b)") == If(
        condition=If(
            condition=Identifier('a'),
            true_branch=Identifier('b'),
            false_branch=Identifier('c')
        ),
        true_branch=BinaryOp(
            Identifier('a'),
            '+',
            Literal(2)
        ),
        false_branch=UnaryOp(
            "()",
            BinaryOp(
                Identifier('a'),
                'or',
                Identifier('b')
            )
        )
    )

    assert parse_string("1 + (if a then 2 else 3) * 4") == BinaryOp(
        Literal(1),
        '+',
        BinaryOp(
            UnaryOp(
                "()",
                If(
                    condition=Identifier('a'),
                    true_branch=Literal(2),
                    false_branch=Literal(3)
                )
            ),
            '*',
            Literal(4)
        )
    )

    assert parse_string("if true then f(false)") == If(
        Literal(True),
        Function(
            Identifier('f'),
            [
                Literal(False)
            ]
        )
    )

def test_unary_parsing() -> None:
    assert parse_string("not a + (- bbb5ifnotb)") == BinaryOp(
        UnaryOp(
            'unary_not',
            Identifier('a')
        ),
        '+',
        UnaryOp(
            '()',
            UnaryOp(
                'unary_-',
                Identifier('bbb5ifnotb')
            )
        )
    )

    assert parse_string("not not - (- not a)") == UnaryOp(
        'unary_not',
        UnaryOp(
            'unary_not',
            UnaryOp(
                'unary_-',
                UnaryOp(
                    '()',
                    UnaryOp(
                        'unary_-',
                        UnaryOp(
                            'unary_not',
                            Identifier('a')
                        )
                    )
                )
            )
        )
    )

def test_function_parsing() -> None:
    assert parse_string("f(a)") == Function(
        Identifier('f'),
        [
            Identifier('a')
        ]
    )

    assert parse_string("    f  (1,2,   4,   b     )     ") == Function(
        Identifier('f'),
        [
            Literal(1),
            Literal(2),
            Literal(4),
            Identifier('b')
        ]
    )

    assert parse_string("a + fun (a+b, not c) * 2") == BinaryOp(
        Identifier('a'),
        '+',
        BinaryOp(
            Function(
                Identifier('fun'),
                [
                    BinaryOp(
                        Identifier('a'),
                        '+',
                        Identifier('b')
                    ),
                    UnaryOp(
                        'unary_not',
                        Identifier('c')
                    )
                ]
            ),
            '*',
            Literal(2)
        )
    )

    assert parse_string("coolfunc()") == Function(
        Identifier('coolfunc')
    )

def test_while_parsing() -> None:
    assert parse_string("while true do f(a)") == While(
        Literal(True),
        Function(
            Identifier('f'),
            [
                Identifier('a')
            ]
        )
    )

def test_var_parsing() -> None:
    pass # Kinda tested in block_parsing, that's good enough for me

def test_parsing_precedence() -> None:
    assert parse_string("4 < 5 + 7 / 6") == BinaryOp(
        Literal(4),
        '<',
        BinaryOp(
            Literal(5),
            '+',
            BinaryOp(
                Literal(7),
                '/',
                Literal(6)
            )
        )
    )

    assert parse_string("4 + 3 or 2 == 7 % 5 and 2 > 2") == BinaryOp(
        BinaryOp(
            Literal(4),
            '+',
            Literal(3)
        ),
        'or',
        BinaryOp(
            BinaryOp(
                Literal(2),
                '==',
                BinaryOp(
                    Literal(7),
                    '%',
                    Literal(5)
                )
            ),
            'and',
            BinaryOp(
                Literal(2),
                '>',
                Literal(2)
            )
        )
    )

def test_block_parsing() -> None:
    assert parse_string('''
{
    while f() do {
        var x: Int = 10;
        var y = if g(x) then {
            x = x + 1;
            x
        } else {
            g(x)
        }  # <-- (this semicolon will become optional later)
        g(y);
    };  # <------ (this too)
    123
}
    ''') == Block(
        [
            While(
                Function(Identifier('f')),
                Block(
                    [
                        Var(Identifier('x'), Literal(10), True),
                        Var(
                            Identifier('y'),
                            If(
                                Function(Identifier('g'), [Identifier('x')]),
                                Block(
                                    [
                                        BinaryOp(
                                            Identifier('x'),
                                            '=',
                                            BinaryOp(
                                                Identifier('x'),
                                                '+',
                                                Literal(1)
                                            )
                                        )
                                    ],
                                    Identifier('x')
                                ),
                                Block(
                                    [],
                                    Function(Identifier('g'), [Identifier('x')])
                                )
                            )
                        ),
                        Function(Identifier('g'), [Identifier('y')])
                    ]
                )
            )
        ],
        Literal(123)
    )

def test_trailing_tokens() -> None:
    assert_parse_fail("1 + 2 3")
    assert_parse_fail("* 2")
    assert_parse_fail("1 2 3 4")
    assert_parse_fail("fun())")
    
def test_var_parsing_fail() -> None:
    assert_parse_fail("if var x = 2 then 1")

def test_optional_semicolons() -> None:
    parse_string("{ { a } { b } }")
    assert_parse_fail("{ a b }")
    parse_string("{ if true then { a } b}")
    parse_string("{ if true then { a }; b}")
    assert_parse_fail("{ if true then { a } b c }")
    parse_string("{ if true then { a } b; c}")
    parse_string("{ if true then { a } else { b } c }")
    parse_string("{ { f(a) } { b } }")