from compiler.tokenizer import tokenize
from compiler.classes import *

def test_tokenizer_basics() -> None:
    L = Location('', 0, 0, True)
    assert tokenize('test')[0].location == L
    assert tokenize("if  3\nwhile") == [
        Token('if', 'identifier', L),
        Token('3', 'integer', L),
        Token('while', 'identifier', L)
        ]
    # assert tokenize("a_1_ __main__ 123") == ['a_1_', '__main__', '123']
    return