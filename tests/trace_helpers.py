def semantic_tree(node):
    """Compare fields shared by the formats, excluding gas accounting and log availability."""
    return {
        "type": node.call_type.value,
        "address": node.address.hex(),
        "depth": node.depth,
        "value": node.value,
        "failed": node.failed,
        "input": node.calldata.hex(),
        "output": node.returndata.hex(),
        "calls": [semantic_tree(child) for child in node.calls],
    }
