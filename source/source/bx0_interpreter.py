#!/usr/bin/env python3

"""
BX0 Interpreter

Usage: ./bx0_interpreter.py file1.bx file2.bx ...
"""

from scanner import load_source, lexer
from parser import parser

import sys


# truncate number to [−2^63, 2^63)
def truncate_number(num):
    # truncate to 64 bits
    num = num & 0xffffffffffffffff
    # convert to 2's complement
    if (num & (1 << 63)) != 0:  # if sign bit is set
        num = num - (1 << 64)
    return num


# evaluate the expression node, returns an integer
def evaluate_expression(variables, node):
    # variable access
    if node.opcode == 'var':
        if node.value not in variables.keys():
            print(f"Error: {node.value} is not defined")
            sys.exit(1)
        return variables[node.value]

    # number
    if node.opcode == 'num':
        return node.value

    # binary expression
    if node.opcode == 'binop':
        res = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x // y,   # integer division
            '%': lambda x, y: x % y,
            '&': lambda x, y: x & y,
            '|': lambda x, y: x | y,
            '^': lambda x, y: x ^ y,
            '<<': lambda x, y: x << y,
            '>>': lambda x, y: x >> y,
        }[node.value](evaluate_expression(variables, node.kids[0]), evaluate_expression(variables, node.kids[1]))
        return truncate_number(res)

    # unary expression
    if node.opcode == 'unop':
        res = {
            '-': lambda x: -x,
            '~': lambda x: ~x,
        }[node.value](evaluate_expression(variables, node.kids[0]))
        return truncate_number(res)


# process a statement
def process_stmt(variables, node):
    if node.opcode == 'assign':
        variables[node.kids[0]] = evaluate_expression(variables, node.kids[1])
    else:
        print(evaluate_expression(variables, node.value))


def main():
    """
    The main loop of the interpreter
    """
    for filename in sys.argv[1:]:
        print(f'[[ processing {filename} ]]')
        load_source(filename)

        # list of program variables
        variables = {}

        # loop and process program statements
        stmts = parser.parse(lexer=lexer)
        while stmts.kids:
            process_stmt(variables, stmts.kids[0])
            stmts = stmts.kids[1]


if __name__ == '__main__':
    main()
