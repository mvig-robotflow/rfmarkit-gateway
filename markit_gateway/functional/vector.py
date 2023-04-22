from typing import List, Dict, Any

import numpy as np


def vectorize_to_np(record_list: List[Dict[str, Any]], keys: List[str]) -> Dict[str, np.ndarray]:
    """Vectorizing record

    Args:
        record_list (List[Dict[str, Any]]): List of records, each record is a bundled dictionary
        keys (List[str]): keys to extract from records

    Returns:
        Dict[str, np.ndarray]: A dictionary in which keys are desired and values are numpy arrays
    """
    assert len(keys) > 0
    assert len(record_list) > 0
    res = {}
    for key in keys:
        res[key] = np.expand_dims(np.array([record[key] for record in record_list]), axis=-1)

    # Verify length
    _length: int = len(res[keys[0]])
    for key in keys:
        if _length != len(res[key]):
            raise ValueError("Not every attribute has the same length")

    return res
