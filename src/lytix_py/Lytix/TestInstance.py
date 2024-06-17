import ast, inspect


def StartTest(target):
    res = {}

    def visit_FunctionDef(node):
        res[node.name] = [ast.dump(e) for e in node.decorator_list]

    V = ast.NodeVisitor()
    V.visit_FunctionDef = visit_FunctionDef
    V.visit(compile(inspect.getsource(target), "?", "exec", ast.PyCF_ONLY_AST))
    return res
