# first class patterns and associated matching

# Patterns - data types
# match - takes value, and tuples per arm
# complete match? -> all possible values matched?
# "applying" a pattern -> match? captured values : NoMatchException? NoMatchError? None?


from dataclasses import dataclass
from typing import Literal

class Width:
    def __init__(self, value: int, variable: bool):
        self.value = value
        self.variable = variable

    def __add__(self, other):
        return Width(self.value + other.value, self.variable or other.variable)

class Pattern: pass

@dataclass
class LiteralPattern(Pattern):
    lit: Literal
    width = Width(1, False)

@dataclass
class CapturePattern(Pattern):
    name: str
    width = Width(1, False)

@dataclass
class ListPattern(Pattern):
    patterns: list[Pattern]
    width = Width(1, False)

@dataclass
class WildCardPattern(Pattern):
    width = Width(1, False)

@dataclass
class RepeatedPattern(Pattern):
    name: str
    pattern: Pattern
    width = Width(0, True)

@dataclass
class AlternativePattern(Pattern):
    left: Pattern
    right: Pattern
    width = Width(1, False)

# takes a value and pattern, and returns either a list of values or throws an exception
def apply(value, pattern: Pattern):
    match pattern:
        case LiteralPattern(lit):
            if lit == value:
                return []
            raise Exception("Value did not match pattern.")
        
        case CapturePattern(name):
            return [(name, value)]
        
        case WildCardPattern():
            return []
        
        case RepeatedPattern(name, pattern):
            match value:
                case [*vs]:
                    matches = []
                    i = 0
                    while True:
                        try:
                            matches.append(apply(vs[i], pattern))
                        except:
                            break
                    return [(name, matches)]
                case _: raise Exception("Value is not a list.")


        case ListPattern(patterns):
            # Wildcard, Repeated Literal 0, Wildcard -> 100001 matches, 40004 aswell, 44004 not. 
            match value:
                case [*vs]:
                    width = Width(0, False)
                    for pattern in patterns:
                        width += pattern.width
                    
                    num_values = len(vs)

                    if num_values < width:
                        raise Exception("Less values than pattern expected.")

                    if num_values > width and not width.variable:
                        raise Exception("Pattern expected less values.")

                    if not width.variable:
                        res = []
                        for v, pattern in zip(vs, patterns):
                            res.extend(apply(v, pattern))
                        return res
                    
                    # segment the value list based on the patterns <- ambiguous
                    # try every possible length for the variable patterns?
                case _: raise Exception("Value is not a list.")
