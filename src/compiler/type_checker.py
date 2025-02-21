from __future__ import annotations
import compiler.ast as ast
from compiler.types import *

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

def typecheck(node: ast.Expression, symtab: SymTab) -> Type:
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
            

    return Unit()