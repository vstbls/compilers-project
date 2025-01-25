from compiler.tokenizer import Token
import compiler.ast as ast


def parse(tokens: list[Token]) -> ast.Expression:
    pos = 0

    left_assoc_binaryops = [
        ['or'],
        ['and'],
        ['==', '!='],
        ['<', '<=', '>', '>='],
        ['+', '-'],
        ['*', '/'],
    ]

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
        expr = parse_level(0)
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
        condition = parse_level(0)

        consume('then')
        true_branch = parse_level(0)

        false_branch = None
        if peek().text == 'else':
            consume('else')
            false_branch = parse_level(0)

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
        
        args = [parse_level(0)]
        while peek().text != ')':
            consume(',')
            args.append(parse_level(0))
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
    return parse_level(0)