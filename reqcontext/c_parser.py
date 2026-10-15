"""Optional Tree-sitter C syntax adapter; never compiles or executes sources."""
from functools import lru_cache


@lru_cache(maxsize=1)
def parser():
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_c
    except ImportError:
        return None
    return Parser(Language(tree_sitter_c.language()))


def available():
    return parser() is not None


def functions(source):
    reader = parser()
    if reader is None:
        return []
    data = source.encode("utf-8")
    root = reader.parse(data).root_node
    result = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type != "function_definition":
            stack.extend(reversed(node.named_children))
            continue
        declarator = node.child_by_field_name("declarator")
        # Unexpanded decoration macros may produce a function_definition whose
        # declarator is actually '(void)'. Do not invent a symbol for that parse.
        candidates = [declarator] if declarator is not None else []
        has_function_declarator = False
        while candidates:
            candidate = candidates.pop()
            if candidate.type == "function_declarator":
                has_function_declarator = True
                break
            candidates.extend(candidate.named_children)
        if not has_function_declarator:
            continue
        while declarator is not None and declarator.type != "identifier":
            inner = declarator.child_by_field_name("declarator")
            if inner is None and declarator.named_children:
                inner = declarator.named_children[0]
            declarator = inner
        if declarator is None:
            continue
        name = data[declarator.start_byte:declarator.end_byte].decode("utf-8")
        calls = set()
        pending = list(node.named_children)
        while pending:
            child = pending.pop()
            if child.type == "function_definition":
                stack.append(child)
                continue
            if child.type == "call_expression":
                target = child.child_by_field_name("function")
                if target is not None:
                    calls.add(data[target.start_byte:target.end_byte].decode("utf-8"))
            pending.extend(child.named_children)
        result.append({"symbol": name, "kind": "function", "start": node.start_point.row + 1,
                       "end": node.end_point.row + 1, "calls": calls})
    return result
