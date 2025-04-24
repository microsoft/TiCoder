from execution import test_code
from config import debug_print

def prune_tests_that_dont_pass_code(code_suggestions, test_suggestions, func_name):
    """Prune tests that don't pass code"""
    return_tests = []
    for test_sugg in test_suggestions:
        # the test does not throw an exception for at least one code suggestion
        # we assume there is a single assert statement as the last line to ensure prefix is well-formed
        for code_sugg in code_suggestions:
            result = test_code(test_sugg, code_sugg, func_name)
            passes = result[0] or result[1] == AssertionError
            if passes:
                debug_print("Test passes code")
                return_tests.append(test_sugg)
                break
    print(f"Dynamic pruning removed {len(test_suggestions) - len(return_tests)} / {len(test_suggestions)} number of test suggestions")

    return return_tests


def prune_codes_that_dont_pass_any_tests(code_suggestions, test_suggestions, func_name):
    """Prune codes that don't pass any tests (unsound in that it can remove a correct suggestion)"""
    return_codes = []
    for code_sugg in code_suggestions:
        # the test does not throw an exception for at least one code suggestion
        # we assume there is a single assert statement as the last line to ensure prefix is well-formed
        passes = False
        for test_sugg in test_suggestions:
            result = test_code(test_sugg, code_sugg, func_name)
            passes = passes or result[0] or result[1] == AssertionError
        if passes:
            debug_print("Test passes code")
            return_codes.append(code_sugg)
    return return_codes


