import sys
sys.path.append('src')
from compiler.tokenizer import tokenize
from compiler.parser import parse
import compiler.ast as ast
from compiler.interpreter import interpret, Value

def ps(s: str) -> ast.Expression: return parse(tokenize(s), False)
def ips(s: str) -> Value: return interpret(ps(s))

s = '{ var x = 3; x + 3}'
ips(s)