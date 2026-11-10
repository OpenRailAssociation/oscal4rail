# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
"""Unique rule-ids and Metapath Subset v1 linting (ADR-018 point 2, #71)."""
import copy
import re

import pytest

import metapath_subset
import validate

# --- the linter -----------------------------------------------------------------

INSIDE = [
    "context('location') = 'stop' and context('transport') = 'rail'",
    "context('location') = 'vehicle-interior' and param('fleet-threshold')\n  <= 30",
    "not(context('a') = 'b') or (param('x') >= 1.5 and param('y') != -2)",
    "context('transport') = ('rail', 'bus', 'tram')",
    "context('transport') != ('rail', 'bus')",
    "param('flag') = true()",
    "param('flag') != false()",
    "param('cutover') >= '2026-01-01'",
    "context('a') = 'it''s'",
    'context("a") = "say ""hi"""',
    "((context('a') = 'b'))",
    "context('a')='b'and param('n')<3",
    "1 < param('n')",
]

OUTSIDE = [
    ("doc('http://evil')//statement and current-dateTime() > 1 ((", "('//') is forbidden"),
    ("current-dateTime() > 1", "'current-dateTime()' is forbidden"),
    ("document('x') = 1", "'document()' is forbidden"),
    ("doc('x') = 1", "'doc()' is forbidden"),
    ("//statement = 'x'", "('//') is forbidden"),
    ("../x = 1", "('..') is forbidden"),
    ("a/b = 1", "('/') is forbidden"),
    ("following::x = 1", "('axis::') is forbidden"),
    ("statement = 'x'", "bare name 'statement'"),
    ("my-function('a') = 1", "'my-function()' is not part of Subset v1"),
    ("$x = 1", "variables are not part"),
    ("@id = 'x'", "attribute access is not part"),
    ("context('a')[1] = 'x'", "predicates are not part"),
    ("context('a')", "expected a comparison operator"),
    ("context('a') = ", "found end of expression"),
    ("context('a') = 'b' and", "found end of expression"),
    ("context('a') = 'b' context('c') = 'd'", "unexpected 'context'"),
    ("context(a) = 'b'", "context() takes one quoted name"),
    ("param() = 1", "param() takes one quoted name"),
    ("context('a') < ('a', 'b')", "value list can only be compared with '=' or '!='"),
    ("context('a') = ()", "expected context"),
    ("not context('a') = 'b'", "expected '('"),
    ("context('a') == 'b'", "found '='"),
    ("param('x') = true", "expected '('"),
    ("(context('a') = 'b'", "expected ')'"),
    ("context('a') = 'unterminated", "unterminated string literal"),
    ("context('a') = 'b' ; 1 = 1", "unexpected character ';'"),
    ("", "expression is empty"),
    ("   ", "expression is empty"),
]


@pytest.mark.parametrize("expression", INSIDE)
def test_expression_inside_the_subset_passes(expression):
    result = metapath_subset.lint(expression)
    assert result.ok, result.errors


@pytest.mark.parametrize("expression, expected", OUTSIDE)
def test_expression_outside_the_subset_is_rejected_with_a_reason(expression, expected):
    result = metapath_subset.lint(expression)
    assert not result.ok
    assert len(result.errors) == 1 and expected in result.errors[0], result.errors
    assert result.context_refs == [] and result.param_refs == []


def test_references_are_collected():
    result = metapath_subset.lint("context('a') = 'x' and (param('p') > 1 or context('b') = param('q'))")
    assert result.context_refs == ["a", "b"]
    assert result.param_refs == ["p", "q"]


def test_non_string_expression_is_rejected():
    assert not metapath_subset.lint(None).ok


def test_documented_examples_and_grammar_are_in_sync(repo):
    """The examples in rules-layer.md §5.1 parse, and the EBNF there is the linter's."""
    text = (repo / "docs" / "reference" / "rules-layer.md").read_text(encoding="utf-8")
    examples = re.search(r"### 5\.1 Examples.*?```\n(.*?)```", text, re.S).group(1).strip().splitlines()
    assert len(examples) >= 2
    for expression in examples:
        assert metapath_subset.lint(expression).ok, expression

    def rules(block):
        return [" ".join(line.split()) for line in block.strip().splitlines()]

    documented = re.search(r"```ebnf\n(.*?)```", text, re.S).group(1)
    in_module = metapath_subset.__doc__.split("Standard library only.")[1]
    assert rules(documented) == rules(in_module)


# --- the validator --------------------------------------------------------------

def _validate(rules, catalog, write_yaml):
    write_yaml("example-catalog.yaml", catalog)
    return validate.validate_file(write_yaml("example-rules.yaml", rules), strict=True)["o4r_pass"]


def _rule(rules, rule_id):
    return next(r for r in rules["rule-set"]["rules"] if r["rule-id"] == rule_id)


def _set_expression(rules, rule_id, expression):
    # a new dict: the example shares one applies-when between two rules (YAML anchor)
    _rule(rules, rule_id)["applies-when"] = {"expression": expression}


def test_example_rule_set_passes(example_rules, example_catalog, write_yaml):
    result = _validate(example_rules, example_catalog, write_yaml)
    assert result["status"] == "pass", result["errors"]


def test_duplicate_rule_id_fails(example_rules, example_catalog, write_yaml):
    rules = example_rules["rule-set"]["rules"]
    rules.append(copy.deepcopy(rules[0]))
    result = _validate(example_rules, example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert f"rule {rules[0]['rule-id']}: duplicate rule-id; rule-ids MUST be unique within a rule-set" \
        in result["errors"]


def test_expression_outside_the_subset_fails_validation(example_rules, example_catalog, write_yaml):
    _set_expression(example_rules, "ex-1.1", "doc('http://evil')//statement and current-dateTime() > 1 ((")
    result = _validate(example_rules, example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any(e.startswith("rule ex-1.1: applies-when.expression is not valid Metapath Subset v1:")
               for e in result["errors"])


def test_undeclared_parameter_fails(example_rules, example_catalog, write_yaml):
    _set_expression(example_rules, "ex-1.1", "param('does-not-exist') > 3")
    result = _validate(example_rules, example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert result["errors"] == [
        "rule ex-1.1: applies-when.expression reads param('does-not-exist'), "
        "which is not declared in rule-set.parameters"]


def test_declared_parameter_passes(example_rules, example_catalog, write_yaml):
    _set_expression(example_rules, "ex-1.1", "param('fleet-threshold') > 3")
    assert _validate(example_rules, example_catalog, write_yaml)["status"] == "pass"


def test_rule_set_without_parameters_rejects_any_param_reference(example_rules, example_catalog, write_yaml):
    del example_rules["rule-set"]["parameters"]
    result = _validate(example_rules, example_catalog, write_yaml)
    assert result["status"] == "fail"
    assert any("param('fleet-threshold')" in e for e in result["errors"])
