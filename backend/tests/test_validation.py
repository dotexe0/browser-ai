"""Tests for AI action validation."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import validate_ai_actions


def test_valid_click():
    actions = [{'action': 'click', 'params': {'x': 100, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_click_negative_coords():
    actions = [{'action': 'click', 'params': {'x': -1, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_click_huge_coords():
    actions = [{'action': 'click', 'params': {'x': 99999, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_valid_type():
    actions = [{'action': 'type', 'params': {'text': 'hello'}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_type_empty_text():
    actions = [{'action': 'type', 'params': {'text': ''}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_type_too_long():
    actions = [{'action': 'type', 'params': {'text': 'x' * 20000}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_valid_wait():
    actions = [{'action': 'wait', 'params': {'ms': 1000}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_wait_too_long():
    actions = [{'action': 'wait', 'params': {'ms': 999999}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_unknown_action_stripped():
    actions = [
        {'action': 'click', 'params': {'x': 10, 'y': 20}},
        {'action': 'hack_system', 'params': {}},
        {'action': 'type', 'params': {'text': 'ok'}},
    ]
    result = validate_ai_actions(actions)
    assert len(result) == 2
    assert result[0]['action'] == 'click'
    assert result[1]['action'] == 'type'


def test_non_list_returns_empty():
    assert validate_ai_actions("not a list") == []
    assert validate_ai_actions(None) == []
    assert validate_ai_actions(42) == []


def test_non_dict_items_skipped():
    actions = [{'action': 'click', 'params': {'x': 5, 'y': 5}}, "bad", 42]
    result = validate_ai_actions(actions)
    assert len(result) == 1
