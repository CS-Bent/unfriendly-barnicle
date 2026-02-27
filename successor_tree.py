"""
successor_tree.py

Tree-structured "chunk" for each unique event: builds a tree rooted at a
given event showing the most-common successors at each level.
"""

from collections import Counter


def build_successor_tree(
    graph: dict, root: str, branching: int = 2, depth: int = 4, threshold: int = 1
) -> dict:
    """
    Build a tree (dict) rooted at *root* showing the *branching* most-common
    successors at each level, up to *depth* levels deep.

    Only edges with count >= *threshold* are considered; a branch is pruned
    entirely once no qualifying successors remain.

    Return value structure:
        {
          "name": "<event>",
          "count": <edge weight from parent, None for root>,
          "children": [ <same structure>, ... ]
        }
    """

    def _recurse(node, remaining_depth, visited):
        successors = graph.get(node, Counter())
        children = []
        # filter by threshold before picking top-branching candidates
        qualified = [
            (c, cnt)
            for c, cnt in successors.most_common()
            if cnt >= threshold and c not in visited
        ]
        for child, cnt in qualified[:branching]:
            child_tree = {"name": child, "count": cnt, "children": []}
            if remaining_depth > 1:
                child_tree["children"] = _recurse(
                    child, remaining_depth - 1, visited | {child}
                )
            children.append(child_tree)
        return children

    return {
        "name": root,
        "count": None,
        "children": _recurse(root, depth, {root}),
    }


def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> None:
    connector = "└── " if is_last else "├── "
    count_str = f"  (×{node['count']})" if node["count"] is not None else ""
    print(prefix + (connector if prefix else "") + node["name"] + count_str)
    child_prefix = prefix + ("    " if is_last else "│   ")
    children = node["children"]
    for i, child in enumerate(children):
        print_tree(child, child_prefix, i == len(children) - 1)
