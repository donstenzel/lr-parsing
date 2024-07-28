from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from ansi import Color, arrow, colored

VALID = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/^ ,:"


def indent(string: str):
    return '\n'.join("| " + line for line in string.split('\n'))

class Parser:

    def __init__(self):
        self.remaining_input = []
        self.current_output = []
        self.lookahead = None

    def shift(self):
        self.current_output.append(self.lookahead)
        try:
            self.lookahead = self.remaining_input.pop()
        except:
            self.lookahead = ''

    def reduce(self, rest, reduced):
        self.current_output = rest # this is like popping 'not rest' from the stack
        self.current_output.append(reduced)

    def parse(self, string):
        self.current_output = []
        self.remaining_input = list(reversed(string))
        self.lookahead = self.remaining_input.pop()
        while True:
            match self.current_output:
                case []: self.shift()

                case [*rest, ' ' | '\t' | '\n']:
                    self.current_output.pop()

                case [*rest,
                       'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h' | 'i' | 'j' | 'k' | 'l' | 'm' |
                       'n' | 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z' |
                       'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J' | 'K' | 'L' | 'M' |
                       'N' | 'O' | 'P' | 'Q' | 'R' | 'S' | 'T' | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z' as l]:
                    self.reduce(rest, Letter(l))

                case [*rest, Letter(l), Identifier(i)]:
                    self.reduce(rest, Identifier(l + i))

                case [*rest, Letter(l)]:
                    if self.lookahead.isalpha(): self.shift()
                    else: self.reduce(rest, Identifier(l))

                case [*rest, Identifier('var')]:
                    self.reduce(rest, Keyword('var'))
                case [*rest, Identifier('val')]:
                    self.reduce(rest, Keyword('val'))
                case [*rest, Identifier('fun')]:
                    self.reduce(rest, Keyword('fun'))

                case [*rest, Identifier(i), ':', Identifier(t)]:
                    self.reduce(rest, TypedIdentifier(i, t))

                case [*rest, '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' as d]:
                    self.reduce(rest, Digit(d))

                case [*rest, Digit(d1), Digit(d2)]:
                    self.reduce(rest, Digit(d1 + d2))

                case [*rest, Digit(d)]:
                    if self.lookahead.isdigit() or self.lookahead == ' ': self.shift()
                    else: self.reduce(rest, Number(int(d)))

                case [*rest, Expression() as l, '^', Expression() as r]:
                    match self.lookahead:
                        case '^': self.shift()
                        case _: self.reduce(rest, Binary(l, '^', r))

                case [*rest, Expression() as l, '*' | '/' as op, Expression() as r]:
                    match self.lookahead:
                        case '^': self.shift()
                        case _: self.reduce(rest, Binary(l, op, r))

                case [*rest, Expression() as l, '+' | '-' as op, Expression() as r]:
                    match self.lookahead:
                        case '*' | '/' | '^': self.shift()
                        case _: self.reduce(rest, Binary(l, op, r))

                case [*rest, Expression() | Declaration() as e1, Expression() | Declaration() as e2]:
                    match self.lookahead:
                        case '(' | ')' | '+' | '-' | '*' | '/' | '^' | '=': self.shift()
                        case _: self.reduce(rest, Block([e1, e2]))

                case [*rest, Block(es), Expression() | Declaration() as e]:
                    self.reduce(rest, Block([*es, e]))

                case [*rest, Expression() as e1, ',', Expression() as e2]:
                    self.reduce(rest, Arguments([e1, e2]))

                case [*rest, Arguments(args), ',', Expression() as arg]:
                    self.reduce(rest, Arguments([*args, arg]))

                case [*rest, TypedIdentifier(_, _) | Identifier(_) as t1, ',', TypedIdentifier(_, _) | Identifier(_) as t2]:
                    self.reduce(rest, Parameters([t1, t2]))

                case [*rest, Parameters(ts), ',', TypedIdentifier(_, _) | Identifier(_) as t]:
                    self.reduce(rest, Parameters([*ts, t]))

                case [*rest, Keyword("var"), Identifier(i), '=', Expression() as e]:
                    self.reduce(rest, Variable(i, e))

                case [*rest, Keyword("val"), Identifier(i), '=', Expression() as e]:
                    self.reduce(rest, Value(i, e))
                
                case [*rest, Keyword("fun"), '(', Parameters(_) as p, ')', '{', Block(_) as b, '}']:
                    self.reduce(rest, AnonymousFunction(p, b))

                case [*rest, Keyword("fun"), '(', Identifier(_) | TypedIdentifier(_, _) as p, ')', '{', Block(_) as b, '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([p]), b))

                case [*rest, Keyword("fun"), '(', ')', '{', Block(_) as b, '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([]), b))

                case [*rest, Keyword("fun"), '(', Parameters(_) as p, ')', '{', Expression() as e, '}']:
                    self.reduce(rest, AnonymousFunction(p, Block([e])))

                case [*rest, Keyword("fun"), '(', Identifier(_) | TypedIdentifier(_, _) as p, ')', '{', Expression() as e, '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([p]), Block([e])))

                case [*rest, Keyword("fun"), '(', ')', '{', Block(_) | Expression() as e, '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([]), Block([e])))

                case [*rest, Keyword("fun"), '(', Parameters(_) as p, ')', '{', '}']:
                    self.reduce(rest, AnonymousFunction(p, Block([])))

                case [*rest, Keyword("fun"), '(', Identifier(_) | TypedIdentifier(_, _) as p, ')', '{', '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([p]), Block([])))

                case [*rest, Keyword("fun"), '(', ')', '{', '}']:
                    self.reduce(rest, AnonymousFunction(Parameters([]), Block([])))

                case [*rest, Identifier(_) | Application(_, _) as f, '(', Arguments(_) as args, ')']:
                    self.reduce(rest, Application(f, args))

                case [*rest, Identifier(_) | Application(_, _) as f, '(', Expression() as e, ')']:
                    self.reduce(rest, Application(f, Arguments([e])))

                case [*rest, Identifier(_) | Application(_, _) as f, '(', ')']:
                    self.reduce(rest, Application(f, Arguments([])))

                case [*_]:
                    match self.lookahead:
                        case '': return self.current_output
                        case _: self.shift()

@dataclass
class Scope:
    parent: Scope | None
    members: dict[str, Expression]

    def __contains__(self, item):
        match item in self.members.keys():
            case True: return True
            case False: return False if self.parent is None else (item in self.parent)

    def __getitem__(self, key):
        match key in self.members.keys():
            case True: return self.members[key]
            case False:
                if self.parent is None:
                    raise Exception(f"{key} does not exist in this scope.")
                return self.parent[key]

    def __setitem__(self, key, value):
        self.members[key] = value

def eval(ast, scope):
    match ast:
        case Number(n): return n


class Expression: pass

@dataclass
class Digit:
    d: str

@dataclass
class Number(Expression):
    n: int

    def __repr__(self):
        return str(self.n)

@dataclass
class Letter:
    l: str

@dataclass
class Identifier(Expression):
    i: str

    def __repr__(self):
        return self.i

@dataclass
class Keyword:
    k: str

@dataclass
class Binary(Expression):
    l: Expression
    op: str
    r: Expression

    def __repr__(self):
        return repr_treelike(self.op, [self.l, self.r])
        # return '\n'.join([
        #     self.op,
        #     indent(self.l.__repr__()),
        #     indent(self.r.__repr__())
        #     ])


@dataclass
class TypedIdentifier:
    i: str
    t: str

    def __repr__(self):
        return i + ": " + t

@dataclass
class Parameters:
    params: list[TypedIdentifier | Identifier]

    def __repr__(self):
        return repr_treelike("Parameters", self.params)
        # return '\n'.join([
        #     "Parameters",
        #     *(indent(param.__repr__()) for param in self.params)
        # ])

@dataclass
class Block:
    es: list[Expression | Declaration]

    def __repr__(self):
        return repr_treelike("Block", self.es)

@dataclass
class AnonymousFunction(Expression):
    params: Parameters
    block: Block

@dataclass
class Arguments:
    args: list[Expression]

@dataclass
class Application(Expression):
    fun: Identifier | Application
    args: Arguments

class Declaration: pass

@dataclass
class Variable(Declaration):
    n: str
    curr_v: Expression

@dataclass
class Value(Declaration):
    n: str
    v: Expression

@dataclass
class Function(Declaration):
    n: str
    params: Parameters
    block: Block

    def __repr__(self):
        return repr_treelike("Function", [self.n, self.params, self.block])
        # return '\n'.join([
        #     "Function",
        #     indent(self.n),
        #     indent(self.params.__repr__()),
        #     indent(self.block.__repr__())
        # ])

def padl(w: int, string: str, padding: str):
    current_w = len(string)
    if current_w < w:
        d = w - current_w
        return padding * d + string

def padr(w: int, string: str, padding: str):
    current_w = len(string)
    if current_w < w:
        d = w - current_w
        return string + padding * d

def repr_treelike(label, entries):
    return '\n'.join([
        label,
        *(indent(entry.__repr__()) for entry in entries)
    ])

def handled(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, *kwargs)
        except: return None
    return inner


def main():

    from ansi import Color, arrowed, colored

    c_error = Color(190, 20, 30)
    c_success = Color(10, 160, 30)
    c_bang = Color(140, 20, 190)


    parser = Parser()
    print(arrowed("welcome to bang! enter · to exit.", now= c_bang))
    while True:
        s = input(arrowed("?", now= c_bang) + ' ')
        if s == '·': break
        try:
            succ = parser.parse(s)
            print(arrowed('!', now= c_success), colored(succ, f= c_success))
        except Exception as e:
            print(arrowed('!', now= c_error), colored(e, f= c_error))
    print(arrowed("Goodbye!", now= c_bang))

if __name__ == "__main__":
    main()