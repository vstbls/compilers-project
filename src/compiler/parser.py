from compiler.tokenizer import Token
import compiler.ast as ast


def parse(tokens: list[Token]) -> ast.Expression:
    pos = 0
    
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
        expr = parse_expression()
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
    
    def parse_term() -> ast.Expression:
        left = parse_factor()
        
        while peek().text in ['*', '/']:
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
        
    expression = parse_expression()
    if pos < len(tokens):
        raise ValueError(f'{peek().location}: unexpected token')
    return expression