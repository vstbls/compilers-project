from compiler.tokenizer import Token
import compiler.ast as ast


def parse(tokens: list[Token]) -> ast.Expression:
    pos = 0
    
    def peek() -> Token:
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
            raise ValueError(f'{token.location} expected on of: {comma_separated}')
        nonlocal pos
        pos += 1
        return token
    
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
    
    def parse_term() -> ast.Expression:
        if peek().type == 'int_literal':
            return parse_int_literal()
        elif peek().type == 'identifier':
            return parse_identifier()
        else:
            raise TypeError(f'{peek().location}: expected an integer literal or identifier')
    
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
        
    return parse_expression()