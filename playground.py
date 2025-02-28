import sys
sys.path.append('src')
from compiler.tokenizer import tokenize
from compiler.parser import parse
from compiler.type_checker import typecheck
from compiler import ast, builtins
import compiler.ir_generator as ir
from compiler.interpreter import interpret, Value

def ps(s: str) -> ast.Expression: return parse(tokenize(s), False)
def ips(s: str) -> Value: return interpret(ps(s))
def irs(s: str) -> str: return "\n".join([str(inst)
                                          for inst in ir.generate_ir(
                                              builtins.builtin_var_types,
                                              toast(s))])
def toast(s: str) -> ast.Expression:
    e = ps(s)
    typecheck(e) # Need to perform type checking after parsing to apply types to all nodes
    return e

s = '1 + 2 * 3'