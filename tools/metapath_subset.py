# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Linter for Metapath Subset v1 (ADR-018 point 2; grammar in docs/reference/rules-layer.md §5.2).

Checks that an `applies-when.expression` is inside the subset: it parses under
the grammar and uses no forbidden construct. It does NOT evaluate anything;
evaluation is Layer 4. Standard library only.

    expression  = or-expr ;
    or-expr     = and-expr , { "or" , and-expr } ;
    and-expr    = term , { "and" , term } ;
    term        = "not" , "(" , or-expr , ")"
                | "(" , or-expr , ")"
                | comparison ;
    comparison  = operand , comp-op , operand
                | operand , ( "=" | "!=" ) , value-list ;
    comp-op     = "=" | "!=" | "<" | "<=" | ">" | ">=" ;
    operand     = reference | literal ;
    reference   = ( "context" | "param" ) , "(" , string , ")" ;
    value-list  = "(" , literal , { "," , literal } , ")" ;
    literal     = number | string | boolean ;
    boolean     = "true" , "(" , ")" | "false" , "(" , ")" ;
    number      = [ "-" ] , digit , { digit } , [ "." , digit , { digit } ] ;
    string      = "'" , { character | "''" } , "'"
                | '"' , { character | '""' } , '"' ;
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<number>-?\d+(?:\.\d+)?)
  | (?P<string>'(?:[^']|'')*'|"(?:[^"]|"")*")
  | (?P<name>[A-Za-z_][A-Za-z0-9_.\-]*)
  | (?P<op><=|>=|!=|=|<|>)
  | (?P<punct>[(),])
""", re.VERBOSE)

# Constructs ADR-018 forbids by name. Anything else outside the grammar is
# rejected as well; these get a message that says why.
_FORBIDDEN_SEQUENCES = (
    ("//", "axis navigation ('//') is forbidden"),
    ("::", "axis navigation ('axis::') is forbidden"),
    ("..", "axis navigation ('..') is forbidden"),
    ("/", "path navigation ('/') is forbidden"),
    ("$", "variables are not part of Subset v1"),
    ("@", "attribute access is not part of Subset v1"),
    ("[", "predicates are not part of Subset v1"),
)
_FORBIDDEN_FUNCTIONS = {
    "current-dateTime", "current-date", "current-time", "document", "doc", "doc-available",
    "random-number-generator", "unparsed-text", "environment-variable", "collection",
}
_KEYWORDS = {"and", "or", "not", "context", "param", "true", "false"}


@dataclass
class LintResult:
    """Outcome of linting one expression."""
    errors: list[str] = field(default_factory=list)
    context_refs: list[str] = field(default_factory=list)
    param_refs: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class _SyntaxError(Exception):
    pass


def _string_value(token_text: str) -> str:
    quote = token_text[0]
    return token_text[1:-1].replace(quote * 2, quote)


def _tokenize(expression: str) -> list[tuple[str, str, int]]:
    tokens, pos = [], 0
    while pos < len(expression):
        match = _TOKEN_RE.match(expression, pos)
        if not match:
            for sequence, message in _FORBIDDEN_SEQUENCES:
                if expression.startswith(sequence, pos):
                    raise _SyntaxError(f"{message} (position {pos + 1})")
            if expression[pos] in "'\"":
                raise _SyntaxError(f"unterminated string literal (position {pos + 1})")
            raise _SyntaxError(f"unexpected character {expression[pos]!r} (position {pos + 1})")
        if match.lastgroup != "ws":
            tokens.append((match.lastgroup, match.group(), pos + 1))
        pos = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[tuple[str, str, int]], result: LintResult):
        self.tokens = tokens
        self.index = 0
        self.result = result

    # -- token helpers -------------------------------------------------------
    def _peek(self, offset: int = 0) -> tuple[str, str, int]:
        i = self.index + offset
        return self.tokens[i] if i < len(self.tokens) else ("end", "", -1)

    def _describe(self, token: tuple[str, str, int]) -> str:
        kind, text, pos = token
        return "end of expression" if kind == "end" else f"{text!r} (position {pos})"

    def _expect(self, text: str) -> None:
        token = self._peek()
        if token[1] != text or token[0] in ("string", "end"):
            raise _SyntaxError(f"expected {text!r}, found {self._describe(token)}")
        self.index += 1

    def _at_keyword(self, word: str) -> bool:
        kind, text, _ = self._peek()
        return kind == "name" and text == word

    # -- grammar -------------------------------------------------------------
    def parse(self) -> None:
        self._or_expr()
        if self._peek()[0] != "end":
            raise _SyntaxError(f"unexpected {self._describe(self._peek())}")

    def _or_expr(self) -> None:
        self._and_expr()
        while self._at_keyword("or"):
            self.index += 1
            self._and_expr()

    def _and_expr(self) -> None:
        self._term()
        while self._at_keyword("and"):
            self.index += 1
            self._term()

    def _term(self) -> None:
        if self._at_keyword("not"):
            self.index += 1
            self._expect("(")
            self._or_expr()
            self._expect(")")
        elif self._peek()[1] == "(" and self._peek()[0] == "punct":
            self.index += 1
            self._or_expr()
            self._expect(")")
        else:
            self._comparison()

    def _comparison(self) -> None:
        self._operand()
        kind, op, _ = self._peek()
        if kind != "op":
            raise _SyntaxError(
                f"expected a comparison operator (=, !=, <, <=, >, >=), found {self._describe(self._peek())}")
        self.index += 1
        if self._peek()[0] == "punct" and self._peek()[1] == "(":
            if op not in ("=", "!="):
                raise _SyntaxError(f"a value list can only be compared with '=' or '!=', not {op!r}")
            self._value_list()
        else:
            self._operand()

    def _value_list(self) -> None:
        self._expect("(")
        self._literal()
        while self._peek()[0] == "punct" and self._peek()[1] == ",":
            self.index += 1
            self._literal()
        self._expect(")")

    def _operand(self) -> None:
        kind, text, _ = self._peek()
        if kind == "name" and text in ("context", "param"):
            self.index += 1
            self._expect("(")
            arg = self._peek()
            if arg[0] != "string":
                raise _SyntaxError(f"{text}() takes one quoted name, found {self._describe(arg)}")
            self.index += 1
            self._expect(")")
            (self.result.context_refs if text == "context" else self.result.param_refs).append(
                _string_value(arg[1]))
        else:
            self._literal()

    def _literal(self) -> None:
        token = self._peek()
        kind, text, _ = token
        if kind in ("number", "string"):
            self.index += 1
        elif kind == "name" and text in ("true", "false"):
            self.index += 1
            self._expect("(")
            self._expect(")")
        elif kind == "name":
            self._reject_name(token)
        else:
            raise _SyntaxError(
                f"expected context('…'), param('…') or a literal, found {self._describe(token)}")

    def _reject_name(self, token: tuple[str, str, int]) -> None:
        _, text, pos = token
        is_call = self._peek(1)[1] == "(" and self._peek(1)[0] == "punct"
        if text in _FORBIDDEN_FUNCTIONS:
            raise _SyntaxError(
                f"function '{text}()' is forbidden: non-deterministic or environment-reading (position {pos})")
        if text in _KEYWORDS:
            raise _SyntaxError(f"unexpected {self._describe(token)}")
        if is_call:
            raise _SyntaxError(
                f"function '{text}()' is not part of Subset v1; only context(), param(), not(), "
                f"true(), false() are allowed (position {pos})")
        raise _SyntaxError(
            f"bare name '{text}' is not part of Subset v1 (no tree navigation; quote strings, "
            f"use context('…') or param('…')) (position {pos})")


def lint(expression: str) -> LintResult:
    """Check one expression against Metapath Subset v1.

    Returns the errors (empty = inside the subset) and the names referenced via
    context() and param(), so the caller can check that they are declared.
    """
    result = LintResult()
    if not isinstance(expression, str) or not expression.strip():
        result.errors.append("expression is empty")
        return result
    try:
        _Parser(_tokenize(expression), result).parse()
    except _SyntaxError as exc:
        result.errors.append(str(exc))
        result.context_refs.clear()
        result.param_refs.clear()
    return result
