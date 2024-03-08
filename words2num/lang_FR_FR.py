from __future__ import division, unicode_literals, print_function
from decimal import Decimal, localcontext
import re

from .core import NumberParseException, placevalue


VOCAB = {
    'zéro': (0, 'Z'),
    'un': (1, 'D'),
    'une': (1, 'D'),
    'deux': (2, 'D'),
    'trois': (3, 'D'),
    'quatre': (4, 'D'),
    'cinq': (5, 'D'),
    'six': (6, 'D'),
    'sept': (7, 'D'),
    'huit': (8, 'D'),
    'neuf': (9, 'D'),
    'dix': (10, 'M'),
    'onze': (11, 'M'),
    'douze': (12, 'M'),
    'treize': (13, 'M'),
    'quatorze': (14, 'M'),
    'quinze': (15, 'M'),
    'seize': (16, 'M'),
    'vingt': (20, 'T'),
    'vingts': (20, 'T'),
    'trente': (30, 'T'),
    'quarante': (40, 'T'),
    'cinquante': (50, 'T'),
    'soixante': (60, 'T'),
    'soixante-dix': (70, 'T'),
    'septante': (70, 'T'),
    'quatre-vingt': (80, 'T'),
    'quatre-vingts': (80, 'T'),
    'huitante': (80, 'T'),
    'quatre-vingt-dix': (90, 'T'),
    'quatre-vingts-dix': (90, 'T'),
    'nonante': (90, 'T'),
    'cent': (100, 'H'),
    'cents': (100, 'H'),
    'mille': (10**3, 'X'),
    'million': (10**6, 'X'),
    'millions': (10**6, 'X'),
    'milliard': (10**9, 'X'),
    'milliards': (10**9, 'X'),
    'billion': (10**12, 'X'),
    'billions': (10**12, 'X'),
    'trillion': (10**18, 'X'),
    'trillions': (10**18, 'X'),
    'quadrillion': (10**24, 'X'),
    'quintillion': (10**30, 'X'),
    'sextillion': (10**36, 'X'),
    'septillion': (10**42, 'X'),
    'octillion': (10**48, 'X'),
    'nonillion': (10**54, 'X'),
    'décillion': (10**60, 'X'),
    'undécillion': (10**66, 'X'),
    'duodécillion': (10**72, 'X'),
    'trédecillion': (10**78, 'X'),
    'quattuordecillion': (10**84, 'X'),
    'quindecillion': (10**90, 'X'),
    'sexdecillion': (10**96, 'X'),
    'septendecillion': (10**102, 'X'),
    'octodecillion': (10**108, 'X'),
    'novemdecillion': (10**114, 'X'),
    'vigintillion': (10**120, 'X'),
    'centillion': (10**303, 'X'),
}


class FST:
    def __init__(self):
        def f_zero(self, n):
            assert n == 0
            self.value = n

        def f_add(self, n):
            self.value += n

        def f_mul(self, n):
            output = self.value * n
            self.value = 0
            return output

        def f_ret(self, _):
            return self.value
        
        def f_ignore(self, n):
            ret = self.value
            self.value = n
            return ret

        self.value = 0
        self.state = 'S'
        self.edges = {
            ('S', 'Z'): f_zero,    # 0
            ('S', 'D'): f_add,     # 9
            ('S', 'T'): f_add,     # 90
            ('S', 'M'): f_add,     # 19
            ('S', 'H'): f_add,     # 100
            ('S', 'F'): f_ret,     # 1
            ('D', 'X'): f_mul,     # 9000
            ('D', 'F'): f_ret,     # 9
            ('D', 'H'): f_mul,     # 201
            ('T', 'D'): f_add,     # 99
            ('T', 'X'): f_mul,     # 90000
            ('T', 'F'): f_ret,     # 90
            ('T', 'M'): f_add,     # 70
            ('M', 'X'): f_mul,     # 19000
            ('M', 'F'): f_ret,     # 19
            ('M', 'D'): f_add,     # 17
            ('H', 'D'): f_add,     # 909
            ('H', 'T'): f_add,     # 990
            ('H', 'M'): f_add,     # 919
            ('H', 'X'): f_mul,     # 900000
            ('H', 'F'): f_ret,     # 900
            ('X', 'D'): f_ignore,     # 9009
            ('X', 'T'): f_add,     # 9090
            ('X', 'M'): f_add,     # 9019
            ('X', 'H'): f_add,     # 9900
            ('X', 'F'): f_ret,     # 9000
            ('Z', 'F'): f_ret,     # 0
            ('S', 'X'): f_add,     # 1000
        }

    def transition(self, token):
        value, label = token
        try:
            edge_fn = self.edges[(self.state, label)]
        except KeyError:
            raise NumberParseException(f"Invalid number state from {self.state} to {label}")

        self.state = label
        return edge_fn(self, value)


def compute_placevalues(tokens):
    """Compute the placevalues for each token in the list tokens"""
    pvs = []
    for tok in tokens:
        if tok in ['point', 'virgule']:
            pvs.append(0)
        else:
            pvs.append(placevalue(VOCAB[tok][0]))
    return pvs

def tokenize(text):
    tokens = re.split(r"[\s,\-]+(?:et)?", text.lower())
    # Remove empty strings caused by split
    tokens = [tok for tok in tokens if tok]

    # Regroup for:
    # 'soixante-dix': (70, 'T'),
    # 'quatre-vingt': (80, 'T'),
    # 'quatre-vingt-dix': (90, 'T'),
    if "soixante" in tokens:
        i = 0
        while i < len(tokens):
            try:
                i = tokens.index("soixante", i)
            except ValueError:
                break
            if i < len(tokens) - 1 and tokens[i + 1] == "dix":
                tokens[i] = "soixante-dix"
                tokens.pop(i + 1)
            i += 1

    for vingt in "vingt", "vingts":
        if vingt in tokens:
            i = 0
            while i < len(tokens):
                try:
                    i = tokens.index(vingt, i)
                except ValueError:
                    break
                if i > 0 and tokens[i - 1] == "quatre":
                    tokens.pop(i)
                    i -= 1
                    if i < len(tokens) - 1 and tokens[i + 1] == "dix":
                        tokens[i] = f"quatre-{vingt}-dix"
                        tokens.pop(i + 1)
                    else:
                        tokens[i] = f"quatre-{vingt}"
                else:
                    i += 1

    # for i, tok in enumerate(tokens):
    try:
        # don't use generator here because we want to raise the exception
        # here now if the word is not found in vocabulary (easier debug)
        decimal = False
        parsed_tokens = []
        decimal_tokens = []
        mul_tokens = []
        pvs = compute_placevalues(tokens)
        # Loop until all trailing multiplier tokens are removed and added to mul_tokens; Loop conditions:
        # 1: The last token in the list must have the highest placevalue of any token
        # 2: The list of tokens must be longer than one (to prevent extracting all tokens as mul_tokens)
        # 3: The maximum placevalue must be greater than 1 (This limits our mul_tokens to "hundred" or greater)
        while max(pvs) == pvs[-1] and len(pvs) > 1 and max(pvs) > 1:
            mul_tokens.insert(0, VOCAB[tokens.pop()])
            pvs.pop()

        for token in tokens:
            if token in ['point', 'virgule']:
                if decimal:
                    raise ValueError(f"Invalid decimal word '{token}'")
                else:
                    decimal = True
            else:
                if decimal:
                    decimal_tokens.append(VOCAB[token])
                else:
                    parsed_tokens.append(VOCAB[token])
    except KeyError as e:
        raise ValueError(f"Invalid number word: {e} in {text}")
    if decimal and not decimal_tokens:
        raise ValueError(f"Invalid sequence: no tokens following 'point'")
    return parsed_tokens, decimal_tokens, mul_tokens


def compute(tokens):
    """Compute the value of given tokens.
    """
    fst = FST()
    outputs = []
    last_placevalue = None
    for token in tokens:
        out = fst.transition(token)
        if out:
            outputs.append(out)
            if last_placevalue and last_placevalue <= placevalue(outputs[-1]):
                raise NumberParseException(f"Invalid sequence {outputs}")
            last_placevalue = placevalue(outputs[-1])
    outputs.append(fst.transition((None, 'F')))
    if last_placevalue and last_placevalue <= placevalue(outputs[-1]):
        raise NumberParseException(f"Invalid sequence {outputs}")
    return sum(outputs)


def compute_multipliers(tokens):
    """
    Determine the multiplier based on the tokens at the end of
    a number (e.g. million from "one thousand five hundred million")
    """
    total = 1
    for token in tokens:
        value, label = token
        total *= value
    return total


def compute_decimal(tokens):
    """Compute value of decimal tokens."""
    with localcontext() as ctx:
        # Locally sets decimal precision to 15 for all computations
        ctx.prec = 15
        total = Decimal()
        place = -1
        for token in tokens:
            value, label = token
            if label not in ('D', 'Z'):
                raise NumberParseException("Invalid sequence after decimal point")
            else:
                total += value * Decimal(10) ** Decimal(place)
                place -= 1
    return float(total) if tokens else 0


def evaluate(text):
    tokens, decimal_tokens, mul_tokens = tokenize(text)
    if not tokens and not decimal_tokens:
        raise ValueError(f"No valid tokens in {text}")

    return (compute(tokens) + compute_decimal(decimal_tokens)) * compute_multipliers(mul_tokens)
