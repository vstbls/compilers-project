from compiler.tokenizer import Token
import compiler.ast as ast


def parse(tokens: list[Token], debug: bool = False) -> ast.Expression:
    pos = 0

    def dprint(s: str):
        if debug: print(s)

    left_assoc_binaryops = [
        ['or'],
        ['and'],
        ['==', '!='],
        ['<', '<=', '>', '>='],
        ['+', '-'],
        ['*', '/'],
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
    
    def parse_parenthesized() -> ast.Expression:
        consume('(')
        expr = parse_expression_nr()
        consume(')')
        return expr
    
    def parse_int_literal() -> ast.Literal:
        if peek().type != 'int_literal':
            raise TypeError(f'{peek().location}: expected an integer literal')
        token = consume()
        return ast.Literal(int(token.text))
    
    def parse_identifier() -> ast.Identifier:
        if peek().type != 'identifier':
            raise TypeError(f'{peek().location}: expected an identifier')
        token = consume()
        return ast.Identifier(token.text)
    
    def parse_factor() -> ast.Expression:
        if peek().text == '(':
            return parse_parenthesized()
        if peek().type == 'int_literal':
            return parse_int_literal()
        elif peek().type == 'identifier':
            return parse_identifier()
        else:
            raise TypeError(f'{peek().location}: expected an integer literal or identifier')

    def parse_if() -> ast.If:
        consume('if')
        condition = parse_expression_nr()

        consume('then')
        true_branch = parse_expression_nr()

        false_branch = None
        if peek().text == 'else':
            consume('else')
            false_branch = parse_expression_nr()

        return ast.If(
            condition,
            true_branch,
            false_branch
        )
    
    def parse_function(id: ast.Identifier) -> ast.Function:
        consume('(')
        if peek().text == ')':
            consume(')')
            return ast.Function(id, [])
        
        args = [parse_expression_nr()]
        while peek().text != ')':
            consume(',')
            args.append(parse_expression_nr())
        consume(')')

        return ast.Function(
            id,
            args
        )

    def parse_term() -> ast.Expression:
        if peek().text == 'if':
            return parse_if()
        
        left = parse_factor()

        if isinstance(left, ast.Identifier) and peek().text == '(':
            left = parse_function(left)
        
        while peek().text in ['*', '/', '%']:
            operator_token = consume()
            operator = operator_token.text
            right = parse_factor()
            left = ast.BinaryOp(
                left,
                operator,
                right
            )

        return left
    
    def parse_expression() -> ast.Expression:
        left = parse_term()
        
        while peek().text in ['+', '-']:
            operator_token = consume()
            operator = operator_token.text
            
            right = parse_term()
            
            left = ast.BinaryOp(
                left,
                operator,
                right
            )
        
        return left

    def parse_level(level: int) -> ast.Expression:
        if level == len(left_assoc_binaryops):
            if peek().text == 'if':
                return parse_if()
            
            expr = parse_factor()

            if isinstance(expr, ast.Identifier) and peek().text == '(':
                expr = parse_function(expr)
            
            return expr

        left = parse_level(level + 1)
        
        while True:
            operator = peek().text
            operator_level = -1

            for i in range(level, len(left_assoc_binaryops)):
                if operator in left_assoc_binaryops[i]:
                    operator_level = i
                    consume(operator)
            if operator_level < 0: break

            right = parse_level(operator_level)

            left = ast.BinaryOp(
                left,
                operator,
                right
            )
        
        return left
    
    def parse_expression_nr() -> ast.Expression: # Non-recursive 
        root = parse_factor()

        while True:
            operator_token = consume()
            operator = operator_token.text
            if operator not in left_prec_level:
                break # Need to fix this, currently can't handle other operators (=, -, ...)
            operator_level = left_prec_level[operator]

            dprint(f'Operator: {operator}, level: {operator_level}')
            
            right = parse_factor()
            
            node = root
            replace_root = False
            while True: # Traverse tree until at the right level
                if not isinstance(node, ast.BinaryOp): # Base case, tree is just the root node
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
                prev_right = node.right
                node.right = ast.BinaryOp(
                    prev_right,
                    operator,
                    right
                )
            
            dprint(f'{root}')

        return root
    
    def parse_expression_right() -> ast.Expression:
        left = parse_factor()

        if peek().text in ['+', '-']:
            operator_token = consume()
            operator = operator_token.text
            
            right = parse_expression_right()
            
            left = ast.BinaryOp(
                left,
                operator,
                right
            )
        
        return left
        
    # expression = parse_expression()
    # if pos < len(tokens):
    #     raise ValueError(f'{peek().location}: unexpected token')
    return parse_expression_nr()