from compiler import ast, ir
from compiler.symtab import SymTab
from compiler.types import Bool, Int, Type, Unit
from compiler.classes import DummyLocation

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
    var_counter = 0
    while ir.IRVar(var_prefix) in root_types.keys():
        var_prefix = '_' + var_prefix
    
    def new_var(t: Type) -> ir.IRVar:
        nonlocal var_counter
        var_counter += 1
        new_var = ir.IRVar(f'{var_prefix}{var_counter}')
        var_types[new_var] = t
        return new_var
    
    label_counter = 0
    def new_label() -> ir.Label:
        nonlocal label_counter
        label_counter += 1
        return ir.Label(DummyLocation(), f'L{label_counter}')

    ins: list[ir.Instruction] = []

    def visit(st: SymTab[ir.IRVar], expr: ast.Expression) -> ir.IRVar:
        loc = expr.location
        match expr:
            case ast.Literal():
                match expr.value:
                    case bool():
                        var = new_var(Bool())
                        ins.append(ir.LoadBoolConst(
                            loc, expr.value, var
                        ))
                    case int():
                        var = new_var(Int())
                        ins.append(ir.LoadIntConst(
                            loc, expr.value, var
                        ))
                    case None:
                        var = var_unit
                    case _:
                        raise TypeError(f'{loc}: unsupported literal: {type(expr.value)}')
                return var
            
            case ast.Identifier():
                return st.require(expr.name)
            
            case ast.BinaryOp():
                if expr.op == '=':
                    var_left = visit(st, expr.left)
                    var_right = visit(st, expr.right)

                    ins.append(ir.Copy(
                        loc, var_left, var_right
                    ))
                    return var_unit
                
                var_op = st.require(expr.op)

                var_left = visit(st, expr.left)
                var_right = visit(st, expr.right)

                var_result = new_var(expr.type)

                ins.append(ir.Call(
                    loc, var_op, [var_left, var_right], var_result
                ))
                return var_result

            case ast.If():
                l_then = new_label()
                l_end = new_label()
                    
                var_cond = visit(st, expr.condition)
                
                if not expr.false_branch:
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_end
                    ))
                    
                    ins.append(l_then)

                    visit(st, expr.true_branch)
                else:
                    l_else = new_label()
                    
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_else
                    ))
                    
                    ins.append(l_then)
                    visit(st, expr.true_branch)
                    ins.append(ir.Jump(
                        loc, l_end
                    ))
                    
                    ins.append(l_else)
                    visit(st, expr.false_branch)
                    
                ins.append(l_end)
                return var_unit

    root_symtab = SymTab[ir.IRVar]()
    for v in root_types.keys():
        root_symtab.set(v.name, v)

    var_final = visit(root_symtab, root_expr)

    if var_types[var_final] == Int:
        pass
    elif var_types[var_final] == Bool:
        pass

    return ins