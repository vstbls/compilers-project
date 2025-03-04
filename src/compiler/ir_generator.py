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
        var_new = ir.IRVar(f'{var_prefix}{var_counter}')
        var_types[var_new] = t
        return var_new
    
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
                var_left = visit(st, expr.left)
                var_right = visit(st, expr.right)
                
                if expr.op == '=':
                    ins.append(ir.Copy(
                        loc, var_right, var_left
                    ))
                    return var_left

                var_result = new_var(expr.type)
                
                if expr.op in ['==', '!=']: # funny special cases
                    var_op = ir.IRVar(expr.op)
                else:
                    var_op = st.require(expr.op)

                ins.append(ir.Call(
                    loc, var_op, [var_left, var_right], var_result
                ))
                return var_result
            
            case ast.UnaryOp():
                var_param = visit(st, expr.param)
                if expr.op == '()':
                    return var_param # Just return the variable of the expression inside the parentheses
                
                var_result = new_var(expr.type)
                ins.append(ir.Call(
                    loc, ir.IRVar(expr.op), [var_param], var_result
                ))
                return var_result

            case ast.If():
                l_then = new_label()
                l_end = new_label()
                    
                var_cond = visit(st, expr.condition)
                
                var_result = var_unit
                
                if not expr.false_branch:
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_end
                    ))
                    
                    ins.append(l_then)

                    visit(st, expr.true_branch)
                else:
                    var_result = new_var(expr.type)
                    
                    l_else = new_label()
                    
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_else
                    ))
                    
                    ins.append(l_then)
                    var_then = visit(st, expr.true_branch)
                    ins.append(ir.Copy(
                        loc, var_then, var_result
                    ))
                    ins.append(ir.Jump(
                        loc, l_end
                    ))
                    
                    ins.append(l_else)
                    var_else = visit(st, expr.false_branch)
                    ins.append(ir.Copy(
                        loc, var_else, var_result
                    ))
                    
                ins.append(l_end)
                return var_result
            
            case ast.Function():
                var_f = st.require(expr.id.name)
                var_args = [visit(st, arg) for arg in expr.args]
                var_result = new_var(expr.type)
                ins.append(ir.Call(
                    loc, var_f, var_args, var_result
                ))
                return var_result
            
            case ast.Block():
                block_st = SymTab[ir.IRVar](st)
                for e in expr.exprs:
                    visit(block_st, e)
                if not expr.res: # Block doesn't have a return expression
                    return var_unit
                return visit(block_st, expr.res)
            
            case ast.While():
                l_loop = new_label()
                l_start = new_label()
                l_end = new_label()

                ins.append(l_loop)
                
                var_cond = visit(st, expr.condition)
                
                ins.append(ir.CondJump(
                    loc, var_cond, l_start, l_end
                ))
                
                ins.append(l_start)

                visit(st, expr.expr)
                
                ins.append(ir.Jump(
                    loc, l_loop
                ))

                ins.append(l_end)
                
                return var_unit
            
            case ast.Var():
                var_expr = visit(st, expr.expr)
                var_result = new_var(expr.expr.type)
                st.define(expr.id.name, var_result)
                ins.append(ir.Copy(
                    loc, var_expr, var_result
                ))
                return var_result
                
        return var_unit

    root_symtab = SymTab[ir.IRVar]()
    for v in root_types.keys():
        root_symtab.set(v.name, v)
        
    ins.append(ir.Label(DummyLocation(), 'start'))

    var_final = visit(root_symtab, root_expr)
    
    if var_types[var_final] == Int():
        ins.append(ir.Call(
            root_expr.location, root_symtab.require('print_int'), [var_final], var_unit
        ))
    elif var_types[var_final] == Bool():
        ins.append(ir.Call(
            root_expr.location, root_symtab.require('print_bool'), [var_final], var_unit
        ))

    return ins