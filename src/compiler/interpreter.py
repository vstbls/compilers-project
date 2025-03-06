from __future__ import annotations
from typing import Any, Callable
from compiler import ast
from compiler.symtab import SymTab
import operator

type Value = int | bool | function | None
        
def read_int() -> int:
    return int(input())

def and_op(a: bool, b: bool) -> bool:
    return a and b

def or_op(a: bool, b: bool) -> bool:
    return a or b

default_symtab: SymTab = SymTab[Value](None, {
    'print_int': print,
    'print_bool': print,
    'read_int': read_int,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.floordiv,
    '%': operator.mod,
    '<': operator.lt,
    '>': operator.gt,
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '>=': operator.ge,
    'and': and_op,
    'or': or_op,
})

def interpret(node: ast.Expression, symtab: SymTab = default_symtab) -> Value:
    match node:
        case ast.Literal():
            return node.value
        
        case ast.Identifier():
            val = symtab.get(node.name)
            if val is None:
                raise ValueError(f'{node.location}: undefined identifier {node.name}')
            return val
        
        case ast.BinaryOp():
            a: Any = interpret(node.left, symtab)
            if node.op == 'and' and a is False: return False
            if node.op == 'or' and a is True: return True
            b: Any = interpret(node.right, symtab)
            if node.op == '=':
                if not isinstance(node.left, ast.Identifier):
                    raise TypeError(f'{node.location}: left side of assignment isn\'t an identifier')
                else:
                    key = node.left.name
                    if symtab.get(key) is None:
                        raise ValueError(f'{node.location}: undefined variable "{a.name}"')
                    symtab.set(key, b)
                    return b
            op: Any = symtab.get(node.op)
            if op is None:
                raise ValueError(f'{node.location}: undefined operator {node.op}')
            return op(a, b)
        
        case ast.UnaryOp():
            if node.op == 'unary_not':
                return not interpret(node.param, symtab)
            if node.op == 'unary_-':
                param = interpret(node.param, symtab)
                if isinstance(param, int):
                    return -param
                raise TypeError(f'{node.param.location}: expected an integer')
            if node.op == '()':
                return interpret(node.param, symtab)
        
        case ast.If():
            if interpret(node.condition, symtab):
                return interpret(node.true_branch, symtab)
            else:
                if node.false_branch is not None:
                    return interpret(node.false_branch, symtab)
                else:
                    return None
            
        case ast.Function():
            func: Any = symtab.get(node.id.name)
            if callable(func):
                args: list[Value] = [interpret(arg, symtab) for arg in node.args]
                return func(*args) # type: ignore
            raise ValueError(f'{node.location}: undefined function "{node.id}"')
        
        case ast.Block():
            block_st = SymTab[Value](symtab)
            for expr in node.exprs:
                interpret(expr, block_st)
            if node.res is not None:
                return interpret(node.res, block_st)
            return None
            
        case ast.While():
            while interpret(node.condition, symtab):
                interpret(node.expr, symtab)
            return None
        
        case ast.Var():
            symtab.set(node.id.name, interpret(node.expr, symtab))
        
    return None