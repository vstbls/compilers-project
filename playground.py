import sys
sys.path.append('src')
from compiler.tokenizer import tokenize
from compiler.parser import parse
from compiler.type_checker import typecheck_module
from compiler import ast, builtins, assembler
import compiler.ir_generator as ir
from compiler.interpreter import interpret, Value
from compiler.asm_generator import generate_asm

def ps(s: str) -> ast.Module: return parse(tokenize(s), False)
def ips(s: str) -> Value: return interpret(ps(s))
def irs(s: str) -> str: return "\n".join([str(inst)
                                          for instructions in ir.generate_ir(
                                              builtins.builtin_var_types,
                                              toast(s)).values()
                                          for inst in instructions
                                          ])
def toast(s: str) -> ast.Module:
    e = ps(s)
    typecheck_module(e) # Need to perform type checking after parsing to apply types to all nodes
    return e

def asm(s: str) -> str:
    return generate_asm(ir.generate_ir(
        builtins.builtin_var_types,
        toast(s)
    ))

def compile(s: str, f: str) -> None:
    assembler.assemble(asm(s), f)

#print(irs('{var x = 2; x = {var x = 1; x}; x = x + 1}'))
toast('var x = { { print_int(1) } { 2 } } x')