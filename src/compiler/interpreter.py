from __future__ import annotations
from typing import Any, Callable
from compiler import ast
import operator

type Value = int | bool | function | None

class SymTab():
    parent: None | SymTab
    locals: dict[str, Value]
    debug = False
    
    def __init__(self, p: 'SymTab' | None = None, d: dict[str, Value] | None = None):
        if p is not None:
            self.parent = p
        else:
            self.parent = None
        if d is not None:
            self.locals = d
        else:
            self.locals = {}
    
    def get(self, key: str) -> Value | None:
        if key in self.locals:
            if self.debug: print(f'd found {key}:{self.locals[key]} in symtab')
            return self.locals[key]
        elif self.parent is not None:
            if self.debug: print(f'd {key} not in symtab, checking parent')
            return self.parent.get(key)
        if self.debug: print(f"d {key} not in any symtab")
        return None
    
    def set(self, key: str, val: Value) -> None:
        if self.get(key) is None or key in self.locals:
            self.locals[key] = val
        else:
            self.parent.set(key, val)
        if self.debug: print(f'd set {key}: {val}')
        
def read_int() -> int:
    return int(input())

default_symtab: SymTab = SymTab(None, {
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
            if node.op == 'not':
                return not interpret(node.param, symtab)
            if node.op == '-':
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
            block_st = SymTab(symtab)
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