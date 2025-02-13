from compiler.tokenizer import Token
import compiler.ast as ast


def parse(tokens: list[Token], debug: bool = False) -> ast.Expression:
    pos = 0

    def dprint(s: str) -> None:
        if debug: print(s)
        
    def isnt_var(expr: ast.Expression) -> ast.Expression:
        if isinstance(expr, ast.Var):
            raise TypeError('Unexpected variable declaration')
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
        pos += 1
        return token
    
    def parse_parenthesized() -> ast.UnaryOp:
        consume('(')
        expr = isnt_var(parse_assignment())
        consume(')')
        return ast.UnaryOp('()', expr) # Super super hacky solution
    
    def parse_int_literal() -> ast.Literal:
        if peek().type != 'int_literal':
            raise TypeError(f'{peek().location}: expected an integer literal')
        token = consume()
        return ast.Literal(int(token.text))
    
    def parse_bool_literal() -> ast.Literal:
        if peek().type != 'bool_literal':
            raise TypeError(f'{peek().location}: expected a boolean literal')
        token = consume(['true', 'false'])
        return ast.Literal(token.text == 'true')

    def parse_identifier() -> ast.Identifier:
        if peek().type != 'identifier':
            raise TypeError(f'{peek().location}: expected an identifier')
        token = consume()
        return ast.Identifier(token.text)
    
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
        consume('{')

        expressions = []
        result = None
        while peek().text != '}':
            expr = parse_assignment()
            if peek().text == ';':
                consume(';')
                expressions.append(expr)
            else:
                result = expr
                break

        if peek().text != '}':
            raise ValueError(f'{peek().location} expected end of block after result expression')
        consume('}')
        
        return ast.Block(expressions, result)

    def parse_if() -> ast.If:
        consume('if')
        condition = isnt_var(parse_assignment())

        consume('then')
        true_branch = isnt_var(parse_assignment())

        false_branch = None
        if peek().text == 'else':
            consume('else')
            false_branch = isnt_var(parse_assignment())

        return ast.If(
            condition,
            true_branch,
            false_branch
        )
    
    def parse_while() -> ast.While:
        consume('while')
        condition = isnt_var(parse_assignment())

        consume('do')
        expr = isnt_var(parse_assignment())

        return ast.While(condition, expr)

    def parse_var() -> ast.Var:
        consume('var')
        id = parse_identifier()

        consume('=')
        expr = isnt_var(parse_assignment())

        return ast.Var(id, expr)
    
    def parse_function(id: ast.Identifier) -> ast.Function:
        consume('(')
        if peek().text == ')':
            consume(')')
            return ast.Function(id, [])
        
        args = [isnt_var(parse_assignment())]
        while peek().text != ')':
            consume(',')
            args.append(isnt_var(parse_assignment()))
        consume(')')

        return ast.Function(
            id,
            args
        )

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
            # Raise an error if not parsed in a block
            return parse_var()
        
        term = parse_factor()

        if isinstance(term, ast.Identifier) and peek().text == '(':
            term = parse_function(term)

        return term
    
    def parse_unary() -> ast.Expression:
        if peek().text in ['-', 'not']:
            operator_token = consume()
            operator = operator_token.text

            parameter = parse_unary() # Recurse to find the first non-unary token

            return ast.UnaryOp(operator, parameter)
        
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
            else:
                if not isinstance(node, ast.BinaryOp): # This should always be true, but the error checker required it
                    raise TypeError('Tried modifying nonexistent child node of operator')
                prev_right = node.right
                node.right = ast.BinaryOp(
                    prev_right,
                    operator,
                    right
                )
            
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

        return left

    expression = parse_assignment()
    if pos < len(tokens):
        raise ValueError(f'{peek().location}: unexpected token')
    return expression