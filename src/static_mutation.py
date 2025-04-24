import ast
import random
import re

import config
from config import debug_print


def is_valid_python_test(code):
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return 'assert' in code


def is_valid_assert_test(test):
    if not is_valid_python_test(test):
        return is_valid_python_test(remove_last_line(test))
    return True


def remove_last_line(code):
    lines = code.split('\n')
    return '\n'.join(lines[:-1])


def is_trivial_python_function(code):
    """Test if code is trivial python function pass"""
    lines = code.split('\n')
    if lines[-1].strip().startswith('pass'):
        return True
    # check if none of lines has an assert statement
    if 'assert' not in code:
        return True
    return False


def prune_tests_statically(test_suggestions):
    """prune/modify the tests syntactically"""
    original_num_tests = len(test_suggestions)
    test_suggestions = prune_modify_tests(test_suggestions)
    print(f"Finished pruning {original_num_tests - len(test_suggestions)} number of test suggestions ")
    return test_suggestions


def prune_multiple_assert(test_sugg):
    """if single_assert_per_test is true take the prefix of the string upto the second assert statement"""
    if not config.single_assert_per_test:
        return test_sugg

    # find the indices of all the assert statements
    assert_indices = [m.start() for m in re.finditer('assert', test_sugg)]
    if len(assert_indices) <= 1:
        return test_sugg

    # sample randomly from multiple assertions within each test
    if config.multiple_asserts_choice == 'random':
        random_assert = random.randint(1, len(assert_indices))
        random_assert_index = assert_indices[random_assert]
        random_assert_prev_index = assert_indices[random_assert-1]
        test_before_asserts = test_sugg[:assert_indices[0]]
        return test_before_asserts + test_sugg[random_assert_prev_index:random_assert_index]

    # find the index of the second assert statement
    second_assert_index = assert_indices[1]
    return test_sugg[:second_assert_index]


def split_multiple_assert(test_sugg):
    """split multiple-assert tests into single-assert ones"""
    if not config.split_asserts:
        return test_sugg

    # find the indices of all the assert statements
    assert_indices = [m.start() for m in re.finditer('assert', test_sugg)]
    if len(assert_indices) <= 1:
        return test_sugg

    debug_print("-" * 80)
    all_tests = []
    test_before_asserts = test_sugg[:assert_indices[0]]
    for ind in range(len(assert_indices)-1):
        assert_index = assert_indices[ind]
        assert_next_index = assert_indices[ind+1]
        all_tests.append(test_before_asserts + test_sugg[assert_index:assert_next_index])
        debug_print(all_tests[-1])
    all_tests.append(test_before_asserts + test_sugg[assert_indices[len(assert_indices)-1]:])
    debug_print(all_tests[-1])
    debug_print("-" * 80)
    return all_tests


def split_tests(test_suggestions):
    if not config.split_asserts:
        return test_suggestions
    debug_print('Generating New Tests' +  '*' * 80)
    new_suggestions = []
    for suggestion in test_suggestions:
        debug_print('-' * 80)
        debug_print(suggestion)
        new_suggestions.extend(split_multiple_assert(suggestion))
    debug_print('*' * 80)
    # new_suggestions = prune_equivalent_codes(new_suggestions)
    new_suggs = list(sorted(list(set(new_suggestions)), key=new_suggestions.count, reverse=True))
    print(f"Generated {len(new_suggs)} single-assert tests from {len(test_suggestions)} multiple-assert tests")
    return new_suggs


def prune_modify_tests(test_suggestions):
    debug_print('Tests' +  '*' * 80)
    new_suggestions = []
    for suggestion in test_suggestions:
        debug_print('-' * 80)
        debug_print(suggestion)

        # check if test has more than one def
        if suggestion.count('def ') > 1:
            debug_print('Modifying test with more than one def')
            suggestion = 'def ' + suggestion.split('def ')[1]
        # check if it is a trivial function pass
        if is_trivial_python_function(suggestion):
            debug_print("Skipping trivial test function with body pass")
            continue
        # check if suggestion parses using python parser
        if is_valid_python_test(suggestion):
            debug_print("Test  is valid python")
            new_suggestions.append(prune_multiple_assert(suggestion))
        else:
            suggestion = remove_last_line(suggestion)
            if is_valid_python_test(suggestion):
                debug_print(f"Modified Test \n{suggestion}\n is valid python")
                new_suggestions.append(prune_multiple_assert(suggestion))
            else:
                debug_print(f"Modified Test \n{suggestion}\n is not valid python")
    debug_print('*' * 80)
    return new_suggestions


def prune_equivalent_codes(codes):
    """Prune equivalent codes"""
    if len(codes) == 0:
        return codes
    new_codes = [codes[0]]
    for code in codes:
        if code not in new_codes:
            new_codes.append(code)
    return new_codes


def prune_equivalent_popular_codes(codes, threshold=1):
    """Prune equivalent codes"""
    if len(codes) == 0:
        return codes, {}
    new_codes = []
    new_stats = {}
    for code in codes:
        new_stats[code] = codes.count(code)
        if code not in new_codes and new_stats[code] <= threshold:
            new_codes.append(code)
    return new_codes, new_stats
