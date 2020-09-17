#!/usr/bin/env python3

"""
Parser built using the PLY/Yacc library
"""

import ply.yacc as yacc

from scanner import tokens, set_source, load_source, lexer, print_error_message

# UMINUS is a **fake** token that is never scanned.
# Its only purpose is to have an entry in the precedence table so that
# when parsing unary minus the precedence for UMINUS can be used instead
# of MINUS (using the directive %prec UMINUS).
tokens += ('UMINUS',)

precedence = (
    ('left', 'BAR'),
    ('left', 'CARET'),
    ('left', 'AMP'),
    ('left', 'LTLT', 'GTGT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH', 'PERCENT'),
    ('left', 'UMINUS'),
    ('left', 'TILDE'),
)


# ------------------------------------------------------------------------------

class Node:
    def __init__(self, opcode, value, *kids):
        self.opcode = opcode
        self.value = value
        self.kids = kids

    def __repr__(self):
        return '({} {}{}{})' \
            .format(self.opcode, repr(self.value),
                    '' if len(self.kids) == 0 else ' ',
                    ' '.join(repr(kid) for kid in self.kids))

    def __eq__(self, other):
        return \
            isinstance(other, Node) and \
            self.opcode == other.opcode and \
            self.value == other.value and \
            self.kids == other.kids


# ------------------------------------------------------------------------------


def p_program(p):
    '''program :
               | stmt program'''

    node = Node('statements', None)
    if len(p) > 1:
        node.kids = (p[1], p[2])
    p[0] = node


def p_stmt(p):
    '''stmt : assign
            | print'''
    p[0] = p[1]


def p_stmt_assign(p):
    '''assign : IDENT EQ expr SEMICOLON'''
    p[0] = Node('assign', '=', p[1], p[3])


def p_stmt_print(p):
    '''print : PRINT LPAREN expr RPAREN SEMICOLON'''
    p[0] = Node('print', p[3])


def p_expr_ident(p):
    '''expr : IDENT'''
    p[0] = Node('var', p[1])


def p_expr_number(p):
    '''expr : NUMBER'''
    p[0] = Node('num', p[1])


def p_expr_binop(p):
    '''expr : expr PLUS  expr
            | expr MINUS expr
            | expr STAR  expr
            | expr SLASH expr
            | expr PERCENT expr
            | expr AMP expr
            | expr BAR expr
            | expr CARET expr
            | expr LTLT expr
            | expr GTGT expr'''
    p[0] = Node('binop', p[2], p[1], p[3])


def p_expr_unop(p):
    '''expr : MINUS expr %prec UMINUS
            | UMINUS expr
            | TILDE expr'''
    p[0] = Node('unop', p[1], p[2])


def p_expr_parens(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]


def p_error(p):
    if not p: return
    print_error_message(p, f'Error: syntax error while processing {p.type}')
    # Note: SyntaxError is a built in exception in Python
    raise SyntaxError(p.type)


parser = yacc.yacc(start='program')

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    from os import devnull


    def parse(source):
        set_source(source)
        with open(devnull, 'w') as lexer.errfile:
            return parser.parse(lexer=lexer)


    import unittest


    class _TestParser(unittest.TestCase):

        def test_print(self):
            source = "print(x);"
            expected = Node('statements', None,
                            Node('print',
                                 Node('var', 'x')),
                            Node('statements', None))

            self.assertEqual(parse(source), expected)

        def test_unary(self):
            source = "print(~3 - -4);"
            expected = Node('statements', None,
                            Node('print',
                                 Node('binop', '-',
                                      Node('unop', '~',
                                           Node('num', 3)),
                                      Node('unop', '-',
                                           Node('num', 4)))),
                            Node('statements', None))

            self.assertEqual(parse(source), expected)

        def test_parens(self):
            source = 's = (x + (y));'
            expected = Node('statements', None,
                            Node('assign', '=',
                                 's',
                                 Node('binop', '+',
                                      Node('var', 'x'),
                                      Node('var', 'y'))),
                            Node('statements', None))

            self.assertEqual(parse(source), expected)

        def test_minus(self):
            source = 's = - w - - w;'
            expected = Node('statements', None,
                            Node('assign', '=', 's',
                                 Node('binop', '-',
                                      Node('unop', '-',
                                           Node('var', 'w')),
                                      Node('unop', '-',
                                           Node('var', 'w')))),
                            Node('statements', None))

            self.assertEqual(parse(source), expected)

        def test_precedence(self):
            source = 's = x + y * z;'
            expected = Node('statements', None,
                            Node('assign', '=', 's',
                                 Node('binop', '+',
                                      Node('var', 'x'),
                                      Node('binop', '*',
                                           Node('var', 'y'),
                                           Node('var', 'z')))),
                            Node('statements', None))

            self.assertEqual(parse(source), expected)

        def test_syntax_error(self):
            source = 's = x + + x;'
            self.assertRaisesRegex(SyntaxError, 'PLUS', parse, source)

    unittest.main()
