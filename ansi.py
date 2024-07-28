from dataclasses import dataclass
from typing import Literal

class NullError(Exception): pass

INVERT = "\033[7m"
INVERT_OFF = "\033[27m"

ARROW_GLYPH = "\ue0b0"

OFF = "\033[0m"

def coalesce(l, r):
    return l if l != None else r

@dataclass
class Color:
    red: int
    green: int
    blue: int
    layer: Literal["FOREGROUND", "BACKGROUND"] = None

    def copy(self, r= None, g= None, b= None, l= None):
        return Color(coalesce(r, self.red), coalesce(g, self.green), coalesce(b, self.blue), coalesce(l, self.layer))

    def background(self):
        return self.copy(l="BACKGROUND")
    
    def foreground(self):
        return self.copy(l="FOREGROUND")

    def __str__(self):
        if not 0 <= self.red <= 255: raise ValueError("Red is not in [0, 255]")
        if not 0 <= self.green <= 255: raise ValueError("Green is not in [0, 255]")
        if not 0 <= self.blue <= 255: raise ValueError("Blue is not in [0, 255]")

        if (self.layer != "FOREGROUND") and (self.layer != "BACKGROUND"):
            raise ValueError("Layer is not foreground or background.")

        match self.layer:
            case "FOREGROUND": n = 38
            case "BACKGROUND": n = 48

        return f"\033[{n};2;{self.red};{self.green};{self.blue}m"

def colored(string: str, f: Color | Literal['']= '', b: Color | Literal['']= ''):
    if f != '': f = f.foreground()
    if b != '': b = b.background()
    return f"{f}{b}{string}{OFF}"

def arrow(f: Color | Literal[''], b: Color | Literal['']):
    return colored(ARROW_GLYPH, f, b)

def arrowed(string, before: Color | Literal['']= '', now: Color | Literal['']= '', after: Color | Literal['']= ''):
    pre = INVERT + arrow(now, before) # cursed
    content = colored(' ' + string + ' ', '', now.background())
    post = arrow(now, after)

    return pre + content + post

def arrowed_many(strs: list[str], base, colors: list[Color | Literal['']]):    
    num_c = len(colors)
    num_s = len(strs)
    res = INVERT + arrow(colors[0], base) # cursed

    *strs, last = strs

    for i, string in enumerate(strs):
        res += colored(f" {string} ", '', colors[i % num_c])   
        res += arrow(colors[i % num_c], colors[(i +1) % num_c])

    res += colored(f" {last} ", '', colors[(num_s -1) % num_c])
    res += arrow(colors[(num_s -1) % num_c], base)

    return res

if __name__ == "__main__":
    c1 = Color(0, 100, 150)
    c2 = Color(100, 50, 50)

    print(arrowed_many(["Hi", "there,", "mom"], '', [c1, c2]))