from typing import Any, Dict, List, Tuple

def find_json_diff(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Compares two JSON objects (dictionaries) and returns a dictionary of changes.

    The returned dictionary maps changed field names to a tuple of (old_value, new_value).
    Only fields present in new_data and different from old_data are included.
    Nested dictionaries are compared recursively.

    Args:
        old_data: The old JSON object.
        new_data: The new JSON object.

    Returns:
        A dictionary where keys are field paths (e.g., 'address.street') and values
        are tuples of (old_value, new_value).
    """
    diff = {}

    def _compare(old_dict: Dict[str, Any], new_dict: Dict[str, Any], path: List[str]):
        for key, new_value in new_dict.items():
            current_path = path + [key]
            full_path = ".".join(current_path)

            if key not in old_dict:
                # New field added
                diff[full_path] = (None, new_value)
            else:
                old_value = old_dict[key]
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    # Recursively compare nested dictionaries
                    _compare(old_value, new_value, current_path)
                elif new_value != old_value:
                    # Field value changed
                    diff[full_path] = (old_value, new_value)
        
        # Check for fields removed from old_data
        for key, old_value in old_dict.items():
            if key not in new_dict:
                full_path = ".".join(path + [key])
                diff[full_path] = (old_value, None)

    _compare(old_data, new_data, [])
    return diff
