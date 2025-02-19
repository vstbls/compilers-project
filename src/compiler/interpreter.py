from typing import Any
from compiler import ast

type Value = int | bool | None

def interpret(node: ast.Expression) -> Value:
    match node:
        case ast.Literal():
            return node.value
        
        case ast.BinaryOp():
            a: Any = interpret(node.left)
            b: Any = interpret(node.right)
            match node.op:
                case '+':
                    return a + b
                case '-':
                    return a - b
                case '*':
                    return a * b
                case '/':
                    return a // b
                case '%':
                    return a % b
                case '<':
                    return a < b
                case '>':
                    return a > b
                case '==':
                    return a == b
                case '!=':
                    return a != b
                case '<=':
                    return a <= b
                case '>=':
                    return a >= b
                case _:
                    raise ValueError(f'{node.location}: invalid operator')
        
        case ast.UnaryOp():
            if node.op == 'not':
                return not interpret(node.param)
            if node.op == '-':
                param = interpret(node.param)
                if param is not None:
                    return -param
            if node.op == '()':
                return interpret(node.param)
        
        case ast.If():
            if interpret(node.condition):
                return interpret(node.true_branch)
            else:
                if node.false_branch is not None:
                    return interpret(node.false_branch)
                else:
                    return None
            
        case ast.While():
            while node.condition:
                interpret(node.expr)
            return None
        
    return None