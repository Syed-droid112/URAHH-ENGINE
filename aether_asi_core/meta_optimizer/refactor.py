"""Concrete AST refactoring transformations."""

import ast
import copy
import logging

logger = logging.getLogger(__name__)


class RemovePassStatements(ast.NodeTransformer):
    """Remove unnecessary `pass` statements from bodies that have other statements."""
    def _clean_body(self, body: list) -> list:
        if len(body) > 1:
            return [stmt for stmt in body if not isinstance(stmt, ast.Pass)]
        return body

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        return node

    def visit_If(self, node):
        self.generic_visit(node)
        node.body = self._clean_body(node.body)
        if node.orelse:
            node.orelse = self._clean_body(node.orelse)
        return node


class FoldConstants(ast.NodeTransformer):
    """Fold simple constant binary operations like 1 + 2 -> 3."""
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            try:
                left, right = node.left.value, node.right.value
                if isinstance(node.op, ast.Add):
                    return ast.Constant(value=left + right)
                elif isinstance(node.op, ast.Sub):
                    return ast.Constant(value=left - right)
                elif isinstance(node.op, ast.Mult):
                    return ast.Constant(value=left * right)
                elif isinstance(node.op, ast.Div) and right != 0:
                    return ast.Constant(value=left / right)
                elif isinstance(node.op, ast.FloorDiv) and right != 0:
                    return ast.Constant(value=left // right)
                elif isinstance(node.op, ast.Mod) and right != 0:
                    return ast.Constant(value=left % right)
            except Exception:
                pass
        return node


class RemoveUnusedImports(ast.NodeTransformer):
    """Remove imports that are never referenced in the rest of the module."""
    def visit_Module(self, node):
        self.generic_visit(node)
        # Collect all Name references (excluding import nodes themselves)
        used_names: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                used_names.add(child.id)
            elif isinstance(child, ast.Attribute):
                # Walk up to find root name
                val = child
                while isinstance(val, ast.Attribute):
                    val = val.value
                if isinstance(val, ast.Name):
                    used_names.add(val.id)

        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Import):
                stmt.names = [alias for alias in stmt.names
                              if (alias.asname or alias.name.split('.')[0]) in used_names]
                if stmt.names:
                    new_body.append(stmt)
                else:
                    logger.info("Removed unused import: %s", ast.unparse(stmt))
            elif isinstance(stmt, ast.ImportFrom):
                stmt.names = [alias for alias in stmt.names
                              if (alias.asname or alias.name) in used_names]
                if stmt.names:
                    new_body.append(stmt)
                else:
                    logger.info("Removed unused import: from %s import ...", stmt.module)
            else:
                new_body.append(stmt)
        node.body = new_body
        return node


class SimplifyIfTrue(ast.NodeTransformer):
    """Simplify `if True:` blocks by inlining the body."""
    def visit_If(self, node):
        self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            return node.body  # inline
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            return node.orelse if node.orelse else []
        return node


class EnsureDocstrings(ast.NodeTransformer):
    """Add a placeholder docstring to functions/classes that lack one."""
    def _has_docstring(self, node) -> bool:
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            return True
        return False

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if not self._has_docstring(node):
            docstring = ast.Expr(value=ast.Constant(value=f"TODO: document {node.name}"))
            node.body.insert(0, docstring)
            logger.info("Added docstring stub to function: %s", node.name)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if not self._has_docstring(node):
            docstring = ast.Expr(value=ast.Constant(value=f"TODO: document {node.name}"))
            node.body.insert(0, docstring)
            logger.info("Added docstring stub to class: %s", node.name)
        return node


# Registry of all transformations in order of application
TRANSFORMS: list[type[ast.NodeTransformer]] = [
    RemovePassStatements,
    FoldConstants,
    RemoveUnusedImports,
    SimplifyIfTrue,
    EnsureDocstrings,
]


def apply_all_transforms(source: str) -> str:
    """Parse source, apply all transforms, return new source."""
    tree = ast.parse(source)
    for transform_cls in TRANSFORMS:
        transformer = transform_cls()
        tree = transformer.visit(tree)
        # visit() on Module with SimplifyIfTrue can return lists; flatten
        if isinstance(tree, list):
            mod = ast.Module(body=[], type_ignores=[])
            for item in tree:
                if isinstance(item, list):
                    mod.body.extend(item)
                else:
                    mod.body.append(item)
            tree = mod
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)
