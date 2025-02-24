from __future__ import annotations
import compiler.ast as ast
from compiler.types import *
from compiler.classes import Location

class SymTab():
    parent: None | SymTab
    locals: dict[str, Type]
    debug = False

    def dprint(self, s: str) -> None:
        if self.debug: print(s)
    
    def __init__(self, p: SymTab | None = None, d: dict[str, Type] | None = None):
        if p is not None:
            self.parent = p
        else:
            self.parent = None
        if d is not None:
            self.locals = d
        else:
            self.locals = {}
    
    def get(self, key: str) -> Type | None:
        if key in self.locals:
            self.dprint(f'd found {key}:{self.locals[key]} in symtab')
            return self.locals[key]
        elif self.parent is not None:
            self.dprint(f'd {key} not in symtab, checking parent')
            return self.parent.get(key)
        self.dprint(f"d {key} not in any symtab")
        return None
    
    def set(self, key: str, type: Type) -> None:
        if self.get(key) is None or key in self.locals:
            self.locals[key] = type
        elif self.parent is not None:
            self.parent.set(key, type)
        self.dprint(f'd set {key}: {type}')
        
default_symtab = SymTab(None, {
    'print_int': FnType([Int()], Unit()),
    'print_bool': FnType([Bool()], Unit()),
    'read_int': FnType([], Int()),
    '+': FnType([Int(), Int()], Int()),
    '-': FnType([Int(), Int()], Int()),
    '*': FnType([Int(), Int()], Int()),
    '/': FnType([Int(), Int()], Int()),
    '%': FnType([Int(), Int()], Int()),
    '<': FnType([Int(), Int()], Bool()),
    '>': FnType([Int(), Int()], Bool()),
    '==': FnType([Int(), Int()], Bool()),
    '!=': FnType([Int(), Int()], Bool()),
    '<=': FnType([Int(), Int()], Bool()),
    '>=': FnType([Int(), Int()], Bool()),
    'and': FnType([Bool(), Bool()], Bool()),
    'or': FnType([Bool(), Bool()], Bool()),
})

def typecheck(node: ast.Expression, symtab: SymTab = default_symtab) -> Type:
    def check_match(where: Location, expected: Type, got: Type):
        if expected != got:
            raise TypeError(f'{where}: expected type {expected}, got {got}')
    
    match node:
        case ast.Literal():
            match node.value:
                case int():
                    return Int()
                case bool():
                    return Bool()
                case None:
                    return Unit()
        
        case ast.Identifier():
            id_type = symtab.get(node.name)
            if id_type is None:
                raise ValueError(f'{node.location}: undefined identifier "{node.name}"')
            return id_type
        
        case ast.BinaryOp():
            t1 = typecheck(node.left)
            t2 = typecheck(node.right)
            if node.op == '=':
                if not isinstance(node.left, ast.Identifier):
                    raise TypeError(f'{node.location}: left side of assignment isn\'t an identifier')
                else:
                    key = node.left.name
                    if symtab.get(key) is None:
                        raise ValueError(f'{node.location}: undefined variable "{node.left.name}"')
                    symtab.set(key, t2)
                    return t2
            op: Type | None = symtab.get(node.op)
            if op is None or not isinstance(op, FnType) or len(op.params) != 2:
                raise ValueError(f'{node.location}: undefined operator "{node.op}"')
            check_match(node.location, op.params[0], t1)
            check_match(node.location, op.params[1], t2)
            return op.res
        
        case ast.UnaryOp():
            t = typecheck(node.param)
            if node.op == 'not':
                check_match(node.location, Bool(), t)
            if node.op == '-':
                check_match(node.location, Int(), t)
            return t
        
        case ast.If():
            check_match(node.location, Bool(), typecheck(node.condition))
            true_t = typecheck(node.true_branch)
            false_t = typecheck(node.false_branch)
            if true_t != false_t:
                raise TypeError(f'{node.location}: mismatching types in conditional branches ({true_t} and {false_t})')
            return true_t
            

    return Unit()