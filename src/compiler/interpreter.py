from typing import Any
from compiler import ast
import operator

type Value = int | bool | function | None

class SymTab():
    parent: None | 'SymTab'
    locals: dict[str, Value]
    
    def __init__(self, p: 'SymTab' | None = None, d: dict[str, Value] | None = None):
        if p is not None:
            self.parent = p
        if d is not None:
            self.locals = d
    
    def get(self, key: str) -> Value | None:
        if key in self.locals:
            return self.locals[key]
        elif self.parent is not None:
            return self.parent.get(key)
        return None
    
    def set(self, key: str, val: Value):
        self.locals[key] = val
        
default_symtab: SymTab = SymTab(None, {
    'print_int': print,
    'print_bool': print,
    'read_int': input,
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
        
        case ast.UnaryOp():
            if node.op == 'not':
                return not interpret(node.param, symtab)
            if node.op == '-':
                param = interpret(node.param, symtab)
                if param is not None:
                    return -param
            if node.op == '()':
                return interpret(node.param, symtab)
        
        case ast.If():
            if interpret(node.condition):
                return interpret(node.true_branch, symtab)
            else:
                if node.false_branch is not None:
                    return interpret(node.false_branch, symtab)
                else:
                    return None
            
        case ast.Function():
            func: function = symtab.get(node.name)
            if func is None:
                raise ValueError(f'{node.location}: undefined function "{node.name}"')
            args: list[Value] = [interpret(arg) for arg in node.args]
            return func(*args)
        
        case ast.Block():
            block_st = SymTab(symtab)
            for expr in node.exprs:
                interpret(expr, block_st)
            if node.res is not None:
                return interpret(node.res)
            return None
            
        case ast.While():
            while node.condition:
                interpret(node.expr, symtab)
            return None
        
        case ast.Var():
            symtab.set(node.id.name, interpret(node.expr, symtab))
        
    return None