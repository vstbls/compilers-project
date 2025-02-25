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
    '<=': FnType([Int(), Int()], Bool()),
    '>=': FnType([Int(), Int()], Bool()),
    'and': FnType([Bool(), Bool()], Bool()),
    'or': FnType([Bool(), Bool()], Bool()),
})

def typecheck(node: ast.Expression, symtab: SymTab = default_symtab) -> Type:
    def check_match(where: Location, expected: Type, got: Type) -> None:
        if expected != got:
            raise TypeError(f'{where}: expected type {expected}, got {got}')
    
    match node:
        case ast.Literal():
            match node.value:
                case bool(): # Check bool first because apparently bool is a subclass of int
                    return Bool()
                case int():
                    return Int()
                case None:
                    return Unit()
        
        case ast.Identifier():
            id_type = symtab.get(node.name)
            if id_type is None:
                raise ValueError(f'{node.location}: undefined identifier "{node.name}"')
            return id_type
        
        case ast.BinaryOp():
            t1 = typecheck(node.left, symtab)
            t2 = typecheck(node.right, symtab)
            if node.op in ['==', '!=']:
                if t1 != t2:
                    raise TypeError(f'{node.location}: comparison\'s types mismatch (got {t1} and {t2})')
                return Bool()
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
            t = typecheck(node.param, symtab)
            if node.op == 'not':
                check_match(node.location, Bool(), t)
            if node.op == '-':
                check_match(node.location, Int(), t)
            return t
        
        case ast.If():
            check_match(node.location, Bool(), typecheck(node.condition, symtab))
            true_t = typecheck(node.true_branch, symtab)
            if node.false_branch is None:
                return Unit()
            false_t = typecheck(node.false_branch, symtab)
            if true_t != false_t:
                raise TypeError(f'{node.location}: mismatching types in conditional branches ({true_t} and {false_t})')
            return true_t
        
        case ast.Function():
            f: Type | None = symtab.get(node.id.name)
            if f is None or not isinstance(f, FnType):
                raise ValueError(f'{node.location}: undefined function "{node.id.name}"')
            if len(node.args) != len(f.params):
                raise ValueError(f'{node.location}: function {node.id.name} takes {f.params}, got {len(node.args)}')
            if f.params != [typecheck(arg, symtab) for arg in node.args]:
                raise ValueError(f'{node.location}: types of arguments don\'t match parameters')
            return f.res
        
        case ast.Block():
            block_st = SymTab(symtab)
            for expr in node.exprs:
                typecheck(expr, block_st)
            if node.res is None:
                return Unit()
            return typecheck(node.res, block_st)

        case ast.While():
            typecheck(node.condition)
            typecheck(node.expr)
            return Unit()
        
        case ast.Var():
            t = typecheck(node.expr, symtab)
            if node.type and node.type != t:
                raise TypeError(f'{node.location}: mismatch between declared type ({node.type}) and actual type ({t})')
            symtab.set(node.id.name, t)
            return Unit()

    return Unit()