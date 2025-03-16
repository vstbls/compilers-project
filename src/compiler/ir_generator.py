from compiler import ast, ir
from compiler.symtab import SymTab
from compiler.types import Bool, Int, Type, Unit
from compiler.classes import DummyLocation
from typing import Any

def generate_ir(
        root_types: dict[ir.IRVar, Type],
        root_node: ast.Module
) -> dict[str, list[ir.Instruction]]:
    var_types: dict[ir.IRVar, Type] = root_types.copy()
    var_defs: dict[ir.IRVar, Type] = {ir.IRVar(d.name) : d.type for d in root_node.defs}
    var_types = var_types | var_defs

    var_unit = ir.IRVar('unit')
    var_types[var_unit] = Unit()
    
    def find_unique(s: str, strings: list[str]) -> str:
        overlap_counter = 1
        res = s
        while res in strings:
            overlap_counter += 1
            res = s + str(overlap_counter)
        return res

    def new_var(t: Type) -> ir.IRVar:
        var_name = find_unique('x', [v.name for v in var_types.keys()])
        var_new = ir.IRVar(var_name)
        var_types[var_new] = t
        return var_new
    
    labels: set[str] = set()
    def new_label(label_name: str = 'label') -> ir.Label:
        label_name = find_unique(label_name, list(labels))
        labels.add(label_name)
        result_label = ir.Label(DummyLocation(), label_name)
        return result_label

    ins: list[ir.Instruction] = []

    def visit(st: SymTab[ir.IRVar], expr: ast.Expression, break_label: None | ir.Label = None, continue_label: None | ir.Label = None) -> ir.IRVar:
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
                var_left = visit(st, expr.left, break_label, continue_label)

                if expr.op in ['and', 'or']:
                    l_right = new_label(f'{expr.op}_right')
                    l_skip = new_label(f'{expr.op}_skip')
                    l_end = new_label(f'{expr.op}_end')
                    
                    if expr.op == 'and':
                        ins.append(ir.CondJump(
                            loc, var_left, l_right, l_skip
                        ))
                    elif expr.op == 'or':
                        ins.append(ir.CondJump(
                            loc, var_left, l_skip, l_right
                        ))

                    ins.append(l_right)

                    var_right = visit(st, expr.right, break_label, continue_label)

                    var_result = new_var(Bool())

                    ins.append(ir.Copy(
                        loc, var_right, var_result
                    ))
                    ins.append(ir.Jump(loc, l_end))

                    ins.append(l_skip)
                    ins.append(ir.LoadBoolConst(
                        loc, expr.op == 'or', var_result
                    ))
                    ins.append(ir.Jump(loc, l_end))

                    ins.append(l_end)
                    return var_result

                var_right = visit(st, expr.right, break_label, continue_label)
                
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
                var_param = visit(st, expr.param, break_label, continue_label)
                if expr.op == '()':
                    return var_param # Just return the variable of the expression inside the parentheses
                
                var_result = new_var(expr.type)
                var_op = st.require(expr.op)
                ins.append(ir.Call(
                    loc, var_op, [var_param], var_result
                ))
                return var_result

            case ast.If():
                l_then = new_label('then')
                l_end = new_label('if_end')
                    
                var_cond = visit(st, expr.condition, break_label, continue_label)
                
                var_result = var_unit
                
                if not expr.false_branch:
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_end
                    ))
                    
                    ins.append(l_then)

                    visit(st, expr.true_branch, break_label, continue_label)
                else:
                    var_result = new_var(expr.type)
                    
                    l_else = new_label('else')
                    
                    ins.append(ir.CondJump(
                        loc, var_cond, l_then, l_else
                    ))
                    
                    ins.append(l_then)
                    var_then = visit(st, expr.true_branch, break_label, continue_label)
                    ins.append(ir.Copy(
                        loc, var_then, var_result
                    ))
                    ins.append(ir.Jump(
                        loc, l_end
                    ))
                    
                    ins.append(l_else)
                    var_else = visit(st, expr.false_branch, break_label, continue_label)
                    ins.append(ir.Copy(
                        loc, var_else, var_result
                    ))
                    
                ins.append(l_end)
                return var_result
            
            case ast.Function():
                var_f = st.require(expr.id.name)
                var_args = [visit(st, arg, break_label, continue_label) for arg in expr.args]
                var_result = new_var(expr.type)
                ins.append(ir.Call(
                    loc, var_f, var_args, var_result
                ))
                return var_result
            
            case ast.Block():
                block_st = SymTab[ir.IRVar](st)
                for e in expr.exprs:
                    visit(block_st, e, break_label, continue_label)
                if not expr.res: # Block doesn't have a return expression
                    return var_unit
                return visit(block_st, expr.res, break_label, continue_label)
            
            case ast.While():
                l_start = new_label('while_start')
                l_body = new_label('while_body')
                l_end = new_label('while_end')

                ins.append(l_start)
                
                var_cond = visit(st, expr.condition, l_end, l_start)
                
                ins.append(ir.CondJump(
                    loc, var_cond, l_body, l_end
                ))
                
                ins.append(l_body)

                visit(st, expr.expr, l_end, l_start)
                
                ins.append(ir.Jump(
                    loc, l_start
                ))

                ins.append(l_end)
                
                return var_unit
            
            case ast.Var():
                var_expr = visit(st, expr.expr, break_label, continue_label)
                var_result = new_var(expr.expr.type)
                st.define(expr.id.name, var_result)
                ins.append(ir.Copy(
                    loc, var_expr, var_result
                ))
                return var_unit

            case ast.Break():
                if not break_label:
                    raise SyntaxError(f'{loc}: break called outside of a loop')
                ins.append(ir.Jump(loc, break_label))
                return var_unit

            case ast.Continue():
                if not continue_label:
                    raise SyntaxError(f'{loc}: continue called outside of a loop')
                ins.append(ir.Jump(loc, continue_label))
                return var_unit
                
        return var_unit

    root_symtab = SymTab[ir.IRVar]()
    for v in root_types.keys():
        root_symtab.set(v.name, v)
    for d in var_defs.keys():
        root_symtab.set(d.name, d)
        
    for d in root_node.defs:
        
        
    ins.append(ir.Label(DummyLocation(), 'start'))

    var_final = visit(root_symtab, root_node.expr)
    
    if var_types[var_final] == Int():
        ins.append(ir.Call(
            root_node.location, root_symtab.require('print_int'), [var_final], var_unit
        ))
    elif var_types[var_final] == Bool():
        ins.append(ir.Call(
            root_node.location, root_symtab.require('print_bool'), [var_final], var_unit
        ))
        
    ins.append(ir.Return(DummyLocation(), None))

    res = {'main': ins}

    return res