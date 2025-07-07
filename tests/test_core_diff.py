"""Tests for the diff engine functionality."""
import pytest
from app.core.diff import find_json_diff


class TestDiffEngine:
    """Test the JSON diff functionality."""
    
    def test_no_changes(self):
        """Test that identical objects return no diff."""
        old_data = {"name": "Acme Corp", "employees": 100}
        new_data = {"name": "Acme Corp", "employees": 100}
        
        diff = find_json_diff(old_data, new_data)
        assert diff == {}
    
    def test_simple_value_change(self):
        """Test simple value changes are detected."""
        old_data = {"name": "Acme Corp", "employees": 100}
        new_data = {"name": "Acme Corp", "employees": 150}
        
        diff = find_json_diff(old_data, new_data)
        assert diff == {"employees": (100, 150)}
    
    def test_new_field_added(self):
        """Test that new fields are detected."""
        old_data = {"name": "Acme Corp"}
        new_data = {"name": "Acme Corp", "employees": 100}
        
        diff = find_json_diff(old_data, new_data)
        assert diff == {"employees": (None, 100)}
    
    def test_field_removed(self):
        """Test that removed fields are detected."""
        old_data = {"name": "Acme Corp", "employees": 100}
        new_data = {"name": "Acme Corp"}
        
        diff = find_json_diff(old_data, new_data)
        assert diff == {"employees": (100, None)}
    
    def test_nested_object_changes(self):
        """Test changes in nested objects."""
        old_data = {
            "name": "Acme Corp",
            "location": {"city": "San Francisco", "state": "CA"}
        }
        new_data = {
            "name": "Acme Corp", 
            "location": {"city": "New York", "state": "NY"}
        }
        
        diff = find_json_diff(old_data, new_data)
        assert diff == {
            "location.city": ("San Francisco", "New York"),
            "location.state": ("CA", "NY")
        }
    
    def test_mixed_changes(self):
        """Test complex scenario with multiple types of changes."""
        old_data = {
            "name": "Acme Corp",
            "employees": 100,
            "location": {"city": "SF"},
            "old_field": "remove_me"
        }
        new_data = {
            "name": "Acme Corp",
            "employees": 150,
            "location": {"city": "SF", "state": "CA"},
            "new_field": "added"
        }
        
        diff = find_json_diff(old_data, new_data)
        expected = {
            "employees": (100, 150),
            "location.state": (None, "CA"),
            "old_field": ("remove_me", None),
            "new_field": (None, "added")
        }
        assert diff == expected
    
    def test_empty_objects(self):
        """Test handling of empty objects."""
        diff = find_json_diff({}, {})
        assert diff == {}
        
        diff = find_json_diff({}, {"new": "value"})
        assert diff == {"new": (None, "value")}
        
        diff = find_json_diff({"old": "value"}, {})
        assert diff == {"old": ("value", None)}
    
    def test_deeply_nested_changes(self):
        """Test changes in deeply nested structures."""
        old_data = {
            "company": {
                "info": {
                    "name": "Acme",
                    "details": {"founded": 2020}
                }
            }
        }
        new_data = {
            "company": {
                "info": {
                    "name": "Acme Corp",
                    "details": {"founded": 2020, "employees": 50}
                }
            }
        }
        
        diff = find_json_diff(old_data, new_data)
        expected = {
            "company.info.name": ("Acme", "Acme Corp"),
            "company.info.details.employees": (None, 50)
        }
        assert diff == expected