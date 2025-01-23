from compiler.tokenizer import tokenize
from compiler.classes import *

def test_tokenizer_basics() -> None:
    L = DummyLocation('', 0, 0) # Dummy location that always evaluates to 'True' on comparison
    assert tokenize('test')[0].location == L
    assert tokenize("a + 5") == [
        Token('a', 'identifier', L),
        Token('+', 'operator', L),
        Token('5', 'int_literal', L)
    ]
    assert tokenize("if  3\nwhile") == [
        Token('if', 'identifier', L),
        Token('3', 'int_literal', L),
        Token('while', 'identifier', L)
        ]
    assert tokenize("a_1_ __main__ 123") == tokenize("a_1_ __main__ 123")
    assert tokenize("a_1_ __main__ 123") == [
        Token('a_1_', 'identifier', L),
        Token('__main__', 'identifier', L),
        Token('123', 'int_literal', L),
    ]
    assert tokenize("if(a==2) {\nreturn a>2; # a stupid function\n}") == [
        Token('if', 'identifier', L),
        Token('(', 'punctuation', L),
        Token('a', 'identifier', L),
        Token('==', 'operator', L),
        Token('2', 'int_literal', L),
        Token(')', 'punctuation', L),
        Token('{', 'punctuation', L),
        Token('return', 'identifier', L),
        Token('a', 'identifier', L),
        Token('>', 'operator', L),
        Token('2', 'int_literal', L),
        Token(';', 'punctuation', L),
        Token('}', 'punctuation', L),
    ]
    return