import random
from collections import defaultdict

import user_interaction as ui
from execution import satisfies_validation_tests, test_code


def rerank_tests(tests, codes, rank_test_option, prog_data):
    if rank_test_option is None:
        return tests

    if rank_test_option == "distinguishing":
        return rank_tests_by_distinguishing_power(tests, codes, prog_data['func_name'])

    if rank_test_option == "distinguishing_simple":
        return rank_tests_by_simple_distinguishing_power(tests, codes, prog_data['func_name'])

    if rank_test_option == "weighted":
        return rank_tests_by_weighted_distinguishing(tests, codes, prog_data['func_name'])

    if rank_test_option == "random":
        return random.sample(tests, len(tests))

    if rank_test_option == "greedy":
        return rank_tests_by_pruned_codes(tests, codes, prog_data)

    if rank_test_option == "ideal":
        return rank_tests_by_pruned_bad_codes(tests, codes, prog_data)

    if rank_test_option == "failed_codes":
        return rank_tests_by_failed_codes(tests, codes, prog_data['func_name'])

    raise NotImplementedError


def rank_tests_by_weighted_distinguishing(tests, codes, func_name):
    """Rank tests based on distinguishing"""
    pass_codes_dict = {}
    fail_codes_dict = {}
    min_supp_tests = {}
    max_supp_tests = {}
    codes_stats = defaultdict((int, int))
    distinguishing_tests = {}
    total_tests = len(tests)
    for test in tests:
        pass_codes = []
        fail_codes = []
        # Expensive operation
        for i, code in enumerate(codes):
            if test_code(test, code, func_name)[0]:
                pass_codes.append(i)
                codes_stats[i] = (codes_stats[code][0] + 1, codes_stats[code][1])
            elif test_code(test, code, func_name)[1] == AssertionError:
                fail_codes.append(i)
                codes_stats[i] = (codes_stats[code][0], codes_stats[code][1] + 1)
        pass_codes_dict[test] = pass_codes
        fail_codes_dict[test] = fail_codes
    for test in tests:
        # distinguishing power of each test
        pass_codes = 0.0
        fail_codes = 0.0
        for code in pass_codes_dict[test]:
            pass_codes += (total_tests - codes_stats[code][0]) * 100 / total_tests
        for code in fail_codes_dict[test]:
            fail_codes += (total_tests - codes_stats[code][1]) * 100 / total_tests
        min_supp_tests[test] = min(pass_codes, fail_codes)
        max_supp_tests[test] = max(1, max(pass_codes, fail_codes)) # should be positive
        distinguishing_tests[test] = min_supp_tests[test] / max_supp_tests[test]
    # sort tests in descending order of distinguishing_tests
    tests = sorted(tests, key=distinguishing_tests.get, reverse=True)
    return tests


def rank_tests_by_failed_codes(tests, codes, func_name):
    """Rank tests based on number of failed codes"""
    pass_codes_dict = {}
    fail_codes_dict = {}
    distinguishing_tests = {}
    total_codes = len(codes)
    for test in tests:
        pass_codes = []
        fail_codes = []
        # Expensive operation
        for code in codes:
            if test_code(test, code, func_name)[0]:
                pass_codes.append(code)
            elif test_code(test, code, func_name)[1] == AssertionError:
                fail_codes.append(code)
        pass_codes_dict[test] = len(pass_codes)
        fail_codes_dict[test] = len(fail_codes)
        # distinguishing power of each test
        distinguishing_tests[test] = (fail_codes_dict[test], total_codes - pass_codes_dict[test])
    # sort tests in descending order of distinguishing_tests
    tests = sorted(tests, key=distinguishing_tests.get, reverse=True)
    return tests


def rank_tests_by_simple_distinguishing_power(tests, codes, func_name):
    """Rank tests based on simple distinguishing power"""
    pass_codes_dict = {}
    fail_codes_dict = {}
    min_supp_tests = {}
    max_supp_tests = {}
    distinguishing_tests = {}
    for test in tests:
        pass_codes = []
        fail_codes = []
        # Expensive operation
        for code in codes:
            if test_code(test, code, func_name)[0]:
                pass_codes.append(code)
            else:
                fail_codes.append(code)
        pass_codes_dict[test] = pass_codes
        fail_codes_dict[test] = fail_codes
        min_supp_tests[test] = min(len(pass_codes), len(fail_codes))
        max_supp_tests[test] = max(1, max(len(pass_codes), len(fail_codes))) # should be positive
        # distinguishing power of each test
        distinguishing_tests[test] = min_supp_tests[test] / max_supp_tests[test]
    # sort tests in descending order of distinguishing_tests
    tests = sorted(tests, key=distinguishing_tests.get, reverse=True)
    return tests


def rank_tests_by_distinguishing_power(tests, codes, func_name):
    """Rank tests based on distinguishing power"""
    pass_codes_dict = {}
    fail_codes_dict = {}
    min_supp_tests = {}
    max_supp_tests = {}
    distinguishing_tests = {}
    for test in tests:
        pass_codes = []
        fail_codes = []
        # Expensive operation
        for code in codes:
            if test_code(test, code, func_name)[0]:
                pass_codes.append(code)
            elif test_code(test, code, func_name)[1] == AssertionError:
                fail_codes.append(code)
        pass_codes_dict[test] = pass_codes
        fail_codes_dict[test] = fail_codes
        min_supp_tests[test] = min(len(pass_codes), len(fail_codes))
        max_supp_tests[test] = max(1, max(len(pass_codes), len(fail_codes))) # should be positive
        # distinguishing power of each test
        distinguishing_tests[test] = min_supp_tests[test] / max_supp_tests[test]
    # sort tests in descending order of distinguishing_tests
    tests = sorted(tests, key=distinguishing_tests.get, reverse=True)
    return tests


def rank_tests_by_pruned_codes(tests, codes, prog_data):
    """Ranks tests based on the number of codes they would prune
       (Greedy ranking)"""
    total_codes = len(codes)
    pruned_tests = {}
    for test in tests:
        ans = ui.query_oracle(test, prog_data)
        if ans == "y":
            pruned_tests[test] = total_codes - len(ui.prune_codes_that_dont_pass_test(test, codes, prog_data))
        elif ans == "n":
            pruned_tests[test] = total_codes - len(ui.prune_codes_that_pass_test(test, codes, prog_data))
        else:
            pruned_tests[test] = 0
    # sort tests in descending order of number of pruned codes
    tests = sorted(tests, key=pruned_tests.get, reverse=True)
    return tests


def rank_tests_by_pruned_bad_codes(tests, codes, prog_data):
    """Ranks tests based on the number of (bad) codes they would prune
       (Ideal ranking)"""
    good_codes = []
    bad_codes = []
    for c in codes:
        if satisfies_validation_tests(c, prog_data):
            good_codes.append(c)
        else:
            bad_codes.append(c)
    total_bad_codes = len(bad_codes)
    pruned_tests = {}
    # if total_bad_codes == 0:
    #     return tests
    for test in tests:
        ans = ui.query_oracle(test, prog_data)
        if ans == "y":
            pruned_tests[test] = (total_bad_codes - len(ui.prune_codes_that_dont_pass_test(test, bad_codes, prog_data)), len(ui.prune_codes_that_dont_pass_test(test, good_codes, prog_data)))
        elif ans == "n":
            pruned_tests[test] = (total_bad_codes - len(ui.prune_codes_that_pass_test(test, bad_codes, prog_data)), len(ui.prune_codes_that_pass_test(test, good_codes, prog_data)))
        else:
            pruned_tests[test] = (0, 0)
    # sort tests in descending order of number of pruned codes
    tests = sorted(tests, key=pruned_tests.get, reverse=True)
    return tests
