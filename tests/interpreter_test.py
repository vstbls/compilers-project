from compiler.tokenizer import tokenize
from compiler.parser import parse
from compiler.interpreter import interpret

def interpret_string(s: str) -> bool | int | None: return interpret(parse(tokenize(s)))

def test_interpret_simple() -> None:
    assert interpret_string("3 + 3") == 6
    assert interpret_string("-1") == -1
    assert interpret_string("- (4 + 3 * 2)") == -10