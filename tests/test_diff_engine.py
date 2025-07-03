import pytest
from app.core.diff import find_json_diff

def test_find_json_diff_no_changes():
    old_data = {"a": 1, "b": "hello", "c": {"d": 4}}
    new_data = {"a": 1, "b": "hello", "c": {"d": 4}}
    diff = find_json_diff(old_data, new_data)
    assert diff == {}

def test_find_json_diff_value_changed():
    old_data = {"a": 1, "b": "hello"}
    new_data = {"a": 2, "b": "world"}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a": (1, 2), "b": ("hello", "world")}

def test_find_json_diff_field_added():
    old_data = {"a": 1}
    new_data = {"a": 1, "b": "new_field"}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"b": (None, "new_field")}

def test_find_json_diff_field_removed():
    old_data = {"a": 1, "b": "old_field"}
    new_data = {"a": 1}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"b": ("old_field", None)}

def test_find_json_diff_nested_value_changed():
    old_data = {"a": {"b": 1, "c": "hello"}}
    new_data = {"a": {"b": 2, "c": "world"}}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a.b": (1, 2), "a.c": ("hello", "world")}

def test_find_json_diff_nested_field_added():
    old_data = {"a": {"b": 1}}
    new_data = {"a": {"b": 1, "c": "new_nested"}}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a.c": (None, "new_nested")}

def test_find_json_diff_nested_field_removed():
    old_data = {"a": {"b": 1, "c": "old_nested"}}
    new_data = {"a": {"b": 1}}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a.c": ("old_nested", None)}

def test_find_json_diff_mixed_changes():
    old_data = {
        "name": "Company A",
        "address": {"street": "123 Main St", "city": "Anytown"},
        "employees": 100,
        "tags": ["tech", "startup"]
    }
    new_data = {
        "name": "Company B",
        "address": {"street": "456 Oak Ave", "zip": "12345"},
        "employees": 120,
        "tags": ["tech", "growth", "saas"],
        "founded_year": 2010
    }
    diff = find_json_diff(old_data, new_data)
    expected_diff = {
        "name": ("Company A", "Company B"),
        "address.street": ("123 Main St", "456 Oak Ave"),
        "address.city": ("Anytown", None),
        "address.zip": (None, "12345"),
        "employees": (100, 120),
        "tags": (["tech", "startup"], ["tech", "growth", "saas"]),
        "founded_year": (None, 2010)
    }
    assert diff == expected_diff

def test_find_json_diff_list_changed():
    old_data = {"items": [1, 2, 3]}
    new_data = {"items": [1, 3, 4]}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"items": ([1, 2, 3], [1, 3, 4])}

def test_find_json_diff_empty_dicts():
    old_data = {}
    new_data = {}
    diff = find_json_diff(old_data, new_data)
    assert diff == {}

def test_find_json_diff_empty_old_data():
    old_data = {}
    new_data = {"a": 1, "b": {"c": 2}}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a": (None, 1), "b": (None, {"c": 2})}

def test_find_json_diff_empty_new_data():
    old_data = {"a": 1, "b": {"c": 2}}
    new_data = {}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"a": (1, None), "b": ({"c": 2}, None)}
