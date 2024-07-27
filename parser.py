import functools
from dataclasses import dataclass
from typing import Iterable
from ansi import Color, arrow, colored

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

    def lex(self, string):
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
                        case  _ : self.reduce(rest, Binary(l, '^', r))

                case [*rest, Expression() as l, '*', Expression() as r]:
                    match self.lookahead:
                        case '^': self.shift()
                        case  _ : self.reduce(rest, Binary(l, '*', r))

                case [*rest, Expression() as l, '+', Expression() as r]:
                    match self.lookahead:
                        case '*': self.shift()
                        case  _ : self.reduce(rest, Binary(l, '+', r))

                case [*rest, Expression() as e1, Expression() as e2]:
                    self.reduce(rest, Expressions([e1, e2]))

                case [*rest, Expressions(es), Expression() as e]:
                    self.reduce(rest, Expressions([*es, e]))

                # case [*rest, TypedIdentifier(_, _) as t]:
                #     if self.lookahead == ',': self.shift()
                #     else: self.reduce(rest, TypedIdentifiers([t]))

                case [*rest, TypedIdentifier(_, _) as t1, ',', TypedIdentifier(_, _) as t2]:
                    self.reduce(rest, TypedIdentifiers([t1, t2]))

                case [*rest, TypedIdentifiers(ts), ',', TypedIdentifier(_, _) as t]:
                    self.reduce(rest, TypedIdentifiers([*ts, t]))

                case [*rest, Keyword("var"), Identifier(i), '=', Expression() as e]:
                    self.reduce(rest, Variable(i, e))

                case [*rest, Keyword("val"), Identifier(i), '=', Expression() as e]:
                    self.reduce(rest, Value(i, e))
                
                case [*rest, Keyword("fun"), '(', TypedIdentifiers(_) | TypedIdentifier(_, _) as t, ')', '{', Expressions(_) | Expression() as e, '}']:
                    self.reduce(rest, Function(t, e))

                case [*rest, Identifier(_) | Function(_, _) as f, '(', Expressions(_) | Expression() as e, ')']:
                    self.reduce(rest, Application(f, e))

                case [*_]:
                    match self.lookahead:
                        case '': return self.current_output
                        case _: self.shift()

class Expression: pass

@dataclass
class Digit:
    d: str

@dataclass
class Number(Expression):
    n: int

@dataclass
class Letter:
    l: str

@dataclass
class Identifier(Expression):
    i: str

@dataclass
class Keyword:
    k: str

@dataclass
class Binary(Expression):
    l: Expression
    op: str
    r: Expression

@dataclass
class TypedIdentifier:
    i: str
    t: str

@dataclass
class TypedIdentifiers:
    ts: list[TypedIdentifier]

@dataclass
class Expressions:
    es: list[Expression]

@dataclass
class Function(Expression):
    params: TypedIdentifiers | TypedIdentifier
    block: Expressions | Expression

@dataclass
class Variable:
    n: str
    curr_v: Expression

@dataclass
class Value:
    n: str
    v: Expression

@dataclass
class Application(Expression):
    fun: Identifier | Function
    args: Expressions | Expression

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


    l = Parser()
    print(arrowed("welcome to bang! enter · to exit.", '', c_bang, ''))
    while True:
        s = input(arrowed("?", '', c_bang, '') + ' ')
        if s == '·': break
        try:
            succ = l.lex(s)
            print(arrowed('!', '', c_success, ''), colored(succ, c_success, ''))
        except Exception as e:
            print(arrowed('!', '', c_error, ''), colored(e, c_error, ''))
    print(arrowed("Goodbye!", '', c_bang, ''))

if __name__ == "__main__":
    main()