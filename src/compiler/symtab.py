from __future__ import annotations
from typing import TypeVar, Generic

T = TypeVar('T')

class SymTab(Generic[T]):
    parent: None | SymTab
    locals: dict[str, T]
    debug = False

    def dprint(self, s: str) -> None:
        if self.debug: print(s)
    
    def __init__(self, p: SymTab | None = None, d: dict[str, T] | None = None):
        if p is not None:
            self.parent = p
        else:
            self.parent = None
        if d is not None:
            self.locals = d
        else:
            self.locals = {}
    
    def get(self, key: str) -> T | None:
        if key in self.locals:
            self.dprint(f'd found {key}:{self.locals[key]} in symtab')
            return self.locals[key]
        elif self.parent is not None:
            self.dprint(f'd {key} not in symtab, checking parent')
            return self.parent.get(key)
        self.dprint(f"d {key} not in any symtab")
        return None
    
    def require(self, key: str) -> T:
        res = self.get(key)
        if not res:
            raise Exception(f'{key} not found in symbol table {type(self)}')
        return res
    
    def set(self, key: str, val: T) -> None:
        if self.get(key) is None or key in self.locals:
            self.locals[key] = val
        elif self.parent is not None:
            self.parent.set(key, val)
        self.dprint(f'd set {key}: {val}')