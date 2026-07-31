"""`code_only` — source with every docstring removed.

⭐ THIS EXISTS BECAUSE THE SAME MISTAKE HAS NOW BEEN MADE FOUR TIMES: a test
searches a module's raw source for a token and matches THE DOCSTRING THAT
EXPLAINS THE RULE IT IS TESTING. Stage 2 hit it, Stage 3 hit it again, the
Decision Record hit it one call site from its own local copy, and B16 hit it
with three copies already in the tree.

⭐ THREE PRIVATE COPIES ARE THREE LISTS THAT AGREE TODAY. It lives here once so
the next test imports it instead of writing a fourth.
"""
import ast
import inspect


def code_only(obj) -> str:
    """Source of a module, class or function with all docstrings stripped."""
    tree = ast.parse(inspect.getsource(obj))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))
