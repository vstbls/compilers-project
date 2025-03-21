from compiler.tokenizer import Token
import compiler.ast as ast
from compiler.types import *


def parse(tokens: list[Token], debug: bool = False) -> ast.Module:
    pos = 0
    prev_token = tokens[0]

    def dprint(s: str) -> None:
        if debug: print(s)
        
    def isnt_var(expr: ast.Expression) -> ast.Expression:
        if isinstance(expr, ast.Var):
            raise TypeError(f'{expr.location}: Unexpected variable declaration')
        return expr

    left_assoc_binaryops = [
        ['or'],
        ['and'],
        ['==', '!='],
        ['<', '<=', '>', '>='],
        ['+', '-'],
        ['*', '/', '%'],
    ]

    left_prec_level: dict[str, int] = {}
    for i in range(len(left_assoc_binaryops)):
        for op in left_assoc_binaryops[i]:
            left_prec_level[op] = i + 1

    def peek() -> Token:
        if len(tokens) == 0:
            raise ValueError('Supplied file is empty')
        nonlocal pos
        if pos < len(tokens):
            return tokens[pos]
        return Token(
            location=tokens[-1].location,
            type="end",
            text="",
        )
    
    def consume(expected: str | list[str] | None = None) -> Token:
        token = peek()
        if isinstance(expected, str) and token.text != expected:
            raise ValueError(f'{token.location} expected "{expected}"')
        if isinstance(expected, list) and token.text not in expected:
            comma_separated = ", ".join(f'"{e}"' for e in expected)
            raise ValueError(f'{token.location} expected one of: {comma_separated}')
        nonlocal pos
        nonlocal prev_token
        pos += 1
        prev_token = token
        return token
    
    def parse_parenthesized() -> ast.UnaryOp:
        loc = consume('(').location
        expr = isnt_var(parse_assignment())
        consume(')')
        ret = ast.UnaryOp('()', expr) # Super super hacky solution
        ret.location = loc
        return ret
    
    def parse_int_literal() -> ast.Literal:
        if peek().type != 'int_literal':
            raise TypeError(f'{peek().location}: expected an integer literal')
        token = consume()
        ret = ast.Literal(int(token.text))
        ret.location = token.location
        return ret
    
    def parse_bool_literal() -> ast.Literal:
        if peek().type != 'bool_literal':
            raise TypeError(f'{peek().location}: expected a boolean literal')
        token = consume(['true', 'false'])
        ret = ast.Literal(token.text == 'true')
        ret.location = token.location
        return ret

    def parse_identifier() -> ast.Identifier:
        if peek().type != 'identifier':
            raise TypeError(f'{peek().location}: expected an identifier')
        token = consume()
        ret = ast.Identifier(token.text)
        ret.location = token.location
        return ret
    
    def parse_factor() -> ast.Expression:
        if peek().type == 'int_literal':
            return parse_int_literal()
        elif peek().type == 'bool_literal':
            return parse_bool_literal()
        elif peek().type == 'identifier':
            return parse_identifier()
        else:
            raise TypeError(f'{peek().location}: expected an integer or boolean literal or identifier')

    def parse_block() -> ast.Block:
        nonlocal prev_token
        loc = consume('{').location

        expressions = []
        result = None
        while peek().text != '}':
            expr = parse_assignment()
            if prev_token.text == '}' or peek().text == ';':
                if peek().text == ';':
                    consume(';')
                expressions.append(expr)
            else:
                result = expr
                break

        if prev_token.text == '}':
            result = expressions.pop()

        if peek().text != '}':
            raise ValueError(f'{peek().location} expected end of block after result expression (are you missing a semicolon?)')
        consume('}')
        
        ret = ast.Block(expressions, result)
        ret.location = loc
        return ret

    def parse_if() -> ast.If:
        loc = consume('if').location
        condition = isnt_var(parse_assignment())

        consume('then')
        true_branch = isnt_var(parse_assignment())

        false_branch = None
        if peek().text == 'else':
            consume('else')
            false_branch = isnt_var(parse_assignment())

        ret = ast.If(
            condition,
            true_branch,
            false_branch
        )
        ret.location = loc
        return ret
    
    def parse_while() -> ast.While:
        loc = consume('while').location
        condition = isnt_var(parse_assignment())

        consume('do')
        expr = isnt_var(parse_assignment())

        ret = ast.While(condition, expr)
        ret.location = loc
        return ret

    def parse_var() -> ast.Var:
        loc = consume('var').location
        id = parse_identifier()
        
        var_type: Type = Unit()
        typed = False
        if peek().text == ':':
            typed = True
            consume(':')
            type_token = consume()
            if type_token.text not in ['Int', 'Bool', 'Unit']:
                raise TypeError(f'{type_token.location}: unrecognized type "{var_type}"')
            match type_token.text:
                case 'Int':
                    var_type = Int()
                case 'Bool':
                    var_type = Bool()

        consume('=')
        expr = isnt_var(parse_assignment())

        ret = ast.Var(id, expr, typed)
        ret.type = var_type
        ret.location = loc
        return ret
    
    def parse_function(id: ast.Identifier) -> ast.Function:
        consume('(')
        if peek().text == ')':
            consume(')')
            ret = ast.Function(id, [])
            ret.location = id.location
            return ret
        
        args = [isnt_var(parse_assignment())]
        while peek().text != ')':
            consume(',')
            args.append(isnt_var(parse_assignment()))
        consume(')')

        ret = ast.Function(
            id,
            args
        )
        ret.location = id.location
        return ret
    
    def parse_return() -> ast.Return:
        loc = consume('return').location
        if peek().text == ';':
            expr = None
        else:
            expr = parse_assignment()
        res = ast.Return(expr)
        res.location = loc
        return res

    def parse_term() -> ast.Expression:
        if peek().text == '{':
            return parse_block()
        if peek().text == '(':
            return parse_parenthesized()
        if peek().text == 'if':
            return parse_if()
        if peek().text == 'while':
            return parse_while()
        if peek().text == 'var':
            return parse_var()
        if peek().text == 'break':
            consume('break')
            return ast.Break()
        if peek().text == 'continue':
            consume('continue')
            return ast.Continue()
        if peek().text == 'return':
            return parse_return()
        
        term = parse_factor()

        if isinstance(term, ast.Identifier) and peek().text == '(':
            term = parse_function(term)

        return term
    
    def parse_unary() -> ast.Expression:
        if peek().text in ['-', 'not']:
            operator_token = consume()
            operator = 'unary_' + operator_token.text

            parameter = parse_unary() # Recurse to find the first non-unary token

            ret = ast.UnaryOp(operator, parameter)
            ret.location = operator_token.location
            return ret
        
        return parse_term()

    def parse_expression() -> ast.Expression: # Non-recursive 
        root = parse_unary()

        while True:
            if peek().text not in left_prec_level:
                break

            operator_token = consume()
            operator = operator_token.text
            operator_level = left_prec_level[operator]

            dprint(f'Operator: {operator}, level: {operator_level}')
            
            right = parse_unary()
            
            node = root
            replace_root = False
            while True: # Traverse tree until at the right level
                if not isinstance(node, ast.BinaryOp): # Base case, tree is just the root node.
                    replace_root = True
                    break
                if not isinstance(node.right, ast.BinaryOp): # The node's right child is a leaf
                    replace_root = left_prec_level[node.op] >= operator_level # This can only evaluate to true if the node is the root
                    break
                if left_prec_level[node.right.op] >= operator_level: break
                node = node.right

            if replace_root:
                root = ast.BinaryOp(
                    root,
                    operator,
                    right
                )
                root.location = operator_token.location
            else:
                if not isinstance(node, ast.BinaryOp): # This should always be true, but the error checker required it
                    raise TypeError('Tried modifying nonexistent child node of operator')
                prev_right = node.right
                node.right = ast.BinaryOp(
                    prev_right,
                    operator,
                    right
                )
                node.right.location = operator_token.location
            
            dprint(f'{root}')

        return root
    
    def parse_assignment() -> ast.Expression:
        left = parse_expression()
        if peek().text == '=':
            operator_token = consume()
            operator = operator_token.text

            right = isnt_var(parse_assignment())

            left = ast.BinaryOp(
                left,
                operator,
                right
            )
            left.location = operator_token.location

        return left
    
    def parse_definition() -> ast.Definition:
        def get_type(s: str) -> Type:
            match s:
                case 'Int':
                    return Int()
                case 'Bool':
                    return Bool()
                case 'Unit':
                    return Unit()
                case _:
                    raise ValueError(f'Unsupported type conversion from string "{s}"')

        consume('fun')

        fun_token = consume()
        fun_name = fun_token.text
        
        consume('(')
        params: list[tuple[ast.Identifier, Type]] = []
        while peek().text != ')':
            param_token = consume()
            param_name = param_token.text
            if param_name in [param[0].name for param in params]:
                raise NameError(f'{param_token.location}: parameter "{param_name}" already used in function definition')
            
            consume(':')

            type_token = consume(['Int', 'Bool', 'Unit'])
            param_type = get_type(type_token.text)
            params.append((ast.Identifier(param_name), param_type))

            if peek().text != ')':
                consume(',')

        consume(')')
        consume(':')

        type_token = consume(['Int', 'Bool', 'Unit'])
        res_type = get_type(type_token.text)

        fun_type = FnType([param[1] for param in params], res_type)

        block = parse_block()

        return ast.Definition(
            fun_name,
            [param[0] for param in params],
            block,
            type=fun_type,
            location=fun_token.location
            )
    
    def parse_top_level() -> ast.Definition | ast.Expression:
        if peek().text == 'fun':
            return parse_definition()
        return parse_assignment()

    defs: list[ast.Definition] = []
    exprs: list[ast.Expression] = []
    
    found_result = False
    ended_with_block = False
    
    # Turns out parsing expressions and definitions separately is unnecessary because
    # definitions are syntactically wrong after any top level expressions. Oh well.
    while pos < len(tokens):
        node = parse_top_level()
        if isinstance(node, ast.Definition):
            defs.append(node)
        else: # Node is an expression
            if found_result:
                raise ValueError(f'{node.location}: result expression already encountered; did you forget a semicolon?')
            exprs.append(node)
            ended_with_block = False
            if prev_token.text == '}':
                if peek().text == ';':
                    consume(';')
                else:
                    ended_with_block = True
            elif peek().text == ';':
                consume(';')
            else:
                found_result = True
           
    result_expr = None
    if found_result or ended_with_block:
        result_expr = exprs.pop()
    
    expr = None
    if len(exprs) == 0 and result_expr:
        expr = result_expr
    elif len(exprs) > 0:
        expr = ast.Block(exprs, result_expr)

    if expr:
        expr.location = tokens[0].location

    module = ast.Module(defs, expr, location=node.location)

    return module