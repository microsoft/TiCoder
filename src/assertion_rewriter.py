import ast
import astunparse
import re
import signal


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)


class Transformer(ast.NodeTransformer):
    def __init__(self, ctxt):
        super().__init__()
        self.in_assert = False
        self.enclosing_func = None
        self.ctxt = ctxt
        self.store = {}

    def visit_Compare(self, node):
        if self.in_assert:
            assert(self.enclosing_func is not None and self.enclosing_func.startswith("test_"))
            assert(len(node.comparators) == 1)
            assert(len(node.ops) == 1)
            op = node.ops[0]
            assert(isinstance(op, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot, ast.Lt, ast.Gt)))
            left = node.left
            code = '_result_ = ' + astunparse.unparse(left)
            loc = {}
            # getting the definition of the function in ctxt
            # print(f"code = {code}, self.ctxt = {self.ctxt}")
            assignments = []
            if isinstance(left, ast.Call):
                args = left.args
                for arg in args:
                    if isinstance(arg, ast.Name) and arg.id in self.store:
                        assignments.append(self.store[arg.id])
            # print(self.ctxt + "\n".join(list(map(astunparse.unparse, assignments))) + code)
            try:
                if assignments:
                    with timeout(seconds=1):
                        exec(self.ctxt + "\n".join(list(map(astunparse.unparse, assignments))) + code, loc)
                else:
                    with timeout(seconds=1):
                        exec(self.ctxt + "\n"  + code, loc)
            except NameError:
                return node
            except Exception:
                return node
            result = loc['_result_']
            if isinstance(result, str):
                result_as_string = repr(result)
            else:
                result_as_string = str(result)

            # Need to remove the default module definition introduced by exec
            replacement = ast.parse(result_as_string).body[0].value
            # return our new compare representation
            # note we do not recurse on "left" or "ops" but reuse them.
            # if they are more complex, this may need to change.
            if isinstance(op, (ast.Lt, ast.Gt)):
                return ast.Compare(
                    left,
                    [ast.Eq()],
                    [replacement])
            else:
                return ast.Compare(
                    left,
                    node.ops,
                    [replacement])

        # not rewriting so continue
        return ast.NodeTransformer.generic_visit(self, node)

    def visit_Assert(self, test):
        # when self.in_assert is true, we rewrite nodes
        # for comparisons (i.e., the test logic of the assert)
        self.in_assert = True
        res = ast.NodeTransformer.generic_visit(self, test)
        self.in_assert = False
        return res

    def visit_FunctionDef(self, node):
        self.enclosing_func = node.name
        ast.NodeTransformer.generic_visit(self, node)
        self.enclosing_func = None
        return node

    def visit_Assign(self, node):
        self.store[node.targets[0].id] = node
        ast.NodeTransformer.generic_visit(self, node)
        return node


def rewrite_assert(ctxt, string):
    """ Rewrite assert statements where the test logic is a simple equality comparison.
        We execute the left hand side of that test and replace the right hand side with
        that execution.

        assert(foo([0,1,2]) == [3,4,5])

        where foo reverses its arguments, thus turns into

        assert(foo([0,1,2]) == [2,1,0])

        Note:
         this code only works for the above pattern. It will rewrite all instances of
         this pattern in string.
         The rewritten spacing may be slightly different than the input but still correct.
    """
    transformer = Transformer(ctxt)
    tree = transformer.visit(ast.parse(string))
    tree = ast.fix_missing_locations(tree)
    rewritten_string = astunparse.unparse(tree)
    asserts = re.findall(r'assert\s*(\(.*\))\s*\r*\n', rewritten_string)
    for asrt in asserts:
        rewritten_string = rewritten_string.replace(asrt, asrt[1:-1])
    return rewritten_string


if __name__ == '__main__':
    # foo must be defined
    # as it is used in the example below
    CTXT = """
def foo(x):
    return list(reversed(x))
"""
    STRING = """
def test_foo():
  setup()
  assert(foo([0,1,2]) == [3,4,5])
  assert(foo([4,5,6]) == [3,4,5])
  x = [5, 6, 4, 2]
  assert (foo(x) == [5, 6, 4, 2]) # this does not work currently
"""
    # rewrite foo([0,1,2]) -> its result from execution
    print('rewriting string:', STRING)
    print()
    print('done:')
    print(rewrite_assert(CTXT, STRING))
