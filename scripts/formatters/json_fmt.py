# -*- coding: utf-8 -*-
"""JSON output formatter."""

import json


def format_json(analysis: dict, indent: int = 2) -> str:
    """Format analysis result as pretty-printed JSON."""
    # Remove large arrays that are not useful in output
    output = _clean_for_output(analysis)
    return json.dumps(output, indent=indent, ensure_ascii=False, default=str)


def _clean_for_output(data: dict) -> dict:
    """Remove internal/large fields not useful for output."""
    cleaned = {}
    skip_keys = {'beat_times'}  # Large arrays
    
    for key, value in data.items():
        if key in skip_keys:
            continue
        if isinstance(value, dict):
            cleaned[key] = _clean_for_output(value)
        elif isinstance(value, list) and len(value) > 50:
            # Truncate very long lists
            cleaned[key] = value[:10]
            cleaned[f'{key}_truncated'] = True
        else:
            cleaned[key] = value
    
    return cleaned
