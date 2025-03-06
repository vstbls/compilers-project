from compiler import ir
from compiler.types import *

builtin_function_types: dict[str, Type] = {
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
    'unary_-': FnType([Int()], Int()),
    'unary_not': FnType([Bool()], Bool())
}

builtin_var_types: dict[ir.IRVar, Type] = {
    ir.IRVar(f): t
    for (f, t) in builtin_function_types.items()
}