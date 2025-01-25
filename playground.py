import sys
sys.path.append('src')
from compiler.tokenizer import tokenize
from compiler.parser import parse
import compiler.ast as ast

def ps(s: str) -> ast.Expression: return parse(tokenize(s), True)