from __future__ import annotations
import compiler.ast as ast
from compiler.types import *
from compiler.classes import Location
from compiler.symtab import SymTab
from compiler.builtins import builtin_function_types

def typecheck_module(module: ast.Module) -> Type:
    symtab = SymTab[Type](None, builtin_function_types.copy())
    
    for d in module.defs:
        definition_symtab = SymTab[Type](symtab)
        typecheck_definition(d, definition_symtab)
    
    module_type = typecheck(module.expr, symtab)
    module.type = module_type
    return module_type

def typecheck_definition(definition: ast.Definition, symtab: SymTab[Type]) -> Type:
    for e in definition.exprs:
        typecheck(e, symtab)

    if definition.res:
        res_type = typecheck(definition.res, symtab)
    else:
        res_type = Unit()

    if isinstance(definition.type, FnType):
        if definition.type.res == res_type:
            return res_type # Maybe makes more sense to return FnType, but tbh the return types aren't even used rn
        else:
            raise TypeError(f'{definition.location}: return type doesn\'t match function definition ({definition.type})')
    else:
        raise ValueError(f'{definition.location}: compiler error, function type set wrong (got {definition.type})')

def typecheck(node: ast.Expression, symtab: SymTab[Type]) -> Type:
    def check_match(where: Location, expected: Type, got: Type) -> None:
        if expected != got:
            raise TypeError(f'{node} at {where}: expected type {expected}, got {got}')
        
    def get_type() -> Type:
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
                        check_match(node.location, t1, t2)
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
                if node.op == 'unary_not':
                    check_match(node.location, Bool(), t)
                if node.op == 'unary_-':
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
                block_st = SymTab[Type](symtab)
                for expr in node.exprs:
                    typecheck(expr, block_st)
                if node.res is None:
                    return Unit()
                return typecheck(node.res, block_st)

            case ast.While():
                check_match(node.location, Bool(), typecheck(node.condition, symtab))
                typecheck(node.expr, symtab)
                return Unit()
            
            case ast.Var():
                if symtab.is_in_scope(node.id.name):
                    raise ValueError(f'{node.location}: Variable "{node.id.name}" already declared in scope')
                t = typecheck(node.expr, symtab)
                if node.typed and node.type != t:
                    raise TypeError(f'{node.location}: mismatch between declared type ({node.type}) and actual type ({t})')
                symtab.define(node.id.name, t)
                return Unit()

        return Unit()
    
    node_type: Type = get_type()
    node.type = node_type
    return node_type