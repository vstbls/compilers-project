from compiler import ast, ir
from compiler.symtab import SymTab
from compiler.types import Bool, Int, Type, Unit

def generate_ir(
        root_types: dict[ir.IRVar, Type],
        root_expr: ast.Expression
) -> list[ir.Instruction]:
    var_types: dict[ir.IRVar, Type] = root_types.copy()

    var_unit = ir.IRVar('unit')
    var_types[var_unit] = Unit()

    # var_prefix used as the prefix for all variables
    # while loop ensures it doesn't collide with variables declared in root_types
    var_prefix = '_x'
    while ir.IRVar(var_prefix) in root_types.keys():
        var_prefix = '_' + var_prefix
    
    def new_var(t: Type) -> ir.IRVar:
        return ir.IRVar('')

    ins: list[ir.Instruction] = []

    def visit(st: SymTab[ir.IRVar], expr: ast.Expression) -> ir.IRVar:
        loc = expr.location
        return ir.IRVar('')

    root_symtab = SymTab[ir.IRVar]()
    for v in root_types.keys():
        root_symtab.set(v.name, v)

    var_final = visit(root_symtab, root_expr)

    if var_types[var_final] == Int:
        pass
    elif var_types[var_final] == Bool:
        pass

    return ins