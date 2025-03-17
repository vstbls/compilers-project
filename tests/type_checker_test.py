from compiler import tokenizer, parser, type_checker
from compiler.types import *

def check_string(s: str) -> Type: return type_checker.typecheck_module(parser.parse(tokenizer.tokenize(s)))

def assert_parse_fail(s: str) -> None:
    try:
        check_string(s)
    except:
        return
    raise AssertionError(f"Type checking didn't fail with input {s}")

def test_type_checking() -> None:
    assert check_string('''
{
    while true do {
        var x = 5;
        x + 5;
        x - 5;
        x % 5;
        x = x = 5;
        x = 5 * 5 + 5 / 5 + (x = 5);
        x = 5;
        var y: Int = -x;
        if not true == false != false and 5 == x then
            (x + y)
        else
            { y = y + 1; x = x - y }
        print_int(x);
        x + y
    }
}
    ''') == Unit()
    
test_type_checking()