import re
from compiler.classes import *

def tokenize(source_code: str) -> list[Token]:
    tokens = {
        'comment': re.compile(r'(#|//).*'),
        'bool_literal': re.compile(r'(true|false)'),
        'identifier': re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'),
        'int_literal': re.compile(r'[0-9]+'),
        'operator': re.compile(r'([=!<>]=|[=*/%<>+-])'),
        'punctuation': re.compile(r'[(){},;]'),
    }
    ws = re.compile(r'(\s|(#|//).*)') # whitespace and comments
    
    res = []
    pos = 0
    while pos < len(source_code):
        ws_match = ws.match(source_code, pos)
        if ws_match:
            pos = ws_match.end()
            continue
        
        matched_token = False
        for token, pattern in tokens.items():
            match = pattern.match(source_code, pos)
            if not match:
                continue
            # Token matched
            matched_token = True
            pos = match.end()
            ln, col = index_to_coordinates(source_code, match.start())
            l = Location('string', ln, col)
            t = Token(match.group(0), token, l)
            res.append(t)
        
        if not matched_token:
            raise(ValueError("Unidentified character at position", pos))
    return res

def index_to_coordinates(s: str, index: int) -> tuple[int, int]:
    # Courtesy of https://stackoverflow.com/a/66443805
    if not len(s):
        return 1, 1
    sp = s[:index+1].splitlines(keepends=True)
    return len(sp), len(sp[-1])