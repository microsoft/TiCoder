import traceback

from assertion_rewriter import rewrite_assert
from config import debug_print
from static_mutation import (prune_equivalent_codes,
                             prune_equivalent_popular_codes,
                             prune_modify_tests)


def cluster_using_regression_tests(code_suggestions, test_suggestions):
    """Cluster the code and tests using regression tests"""

    # the first test may have a form (x = 1; assert(foo(x) ==2)) that cannot be currently rewritten
    # lets try until we have a test for which at least once rewrite succeeds

    regr_test_clusters = {}
    # enumerate test_suggestions
    for (i, test_sugg) in enumerate(test_suggestions):
        if len(regr_test_clusters) > 0:
            debug_print(f"Found a test that can be rewritten after {i} tests")
            break
        for code_sugg in code_suggestions:
            try:
                debug_print(f"Test to rewrite = {test_sugg}")
                t1 = rewrite_assert(code_sugg, test_sugg)
                debug_print(f"Rewritten test = {t1}")
                if t1 in [t[0] for t in regr_test_clusters]:
                    regr_test_clusters[t1].append(code_sugg)
                else:
                    regr_test_clusters[t1] = [code_sugg]
            except:
                debug_print(f"Exception in rewriter: {traceback.format_exc()}")
                continue
    debug_print(f"Number of clusters = {len(regr_test_clusters)}")
    # sort the test clusters by size of code suggestions that are equivalent (largest first)
    sorted_regr_test_clusters = sorted(regr_test_clusters.items(), key=lambda x: len(x[1]), reverse=True)
    # print(f"Sorted Test clusters = {(sorted_regr_test_clusters)}")
    return [t[0] for t in sorted_regr_test_clusters]


def mk_regression_tests(tests_w_code):
    """Make regression tests by updating the oracle with actual runtime values"""
    tests = []
    for (c, t) in tests_w_code:
        try:
            # need to get rid non-parseable lines
            t2 = prune_modify_tests([t])
            if len(t2) == 0:
                continue
            t1 = rewrite_assert(c, t2[0])
            tests.append(t1)
            debug_print(f"rewrote {t} to {t1}")
        except:
            debug_print(f"Exception in mk_regression_tests")
            traceback.print_exc()
            continue
    return tests


def assert_rewrite_all(code_suggestions, test_suggestions):
    """"Pair and run all tests with all code suggestions to generate new tests"""
    test_w_code = [(code_sugg, test_sugg) for code_sugg in code_suggestions for test_sugg in test_suggestions]
    new_test_suggestions = []
    new_test_suggestions.extend(test_suggestions)
    new_test_suggestions.extend(mk_regression_tests(test_w_code))
    return prune_equivalent_codes(new_test_suggestions)


def assert_rewrite_rare(code_suggestions, test_suggestions, top_rare=5):
    """"Pair and run all tests with all code suggestions to generate new tests
        Keep only the a percentage of the rarest new tests"""
    test_w_code = [(code_sugg, test_sugg) for code_sugg in code_suggestions for test_sugg in test_suggestions]
    new_test_suggestions = []
    new_test_suggestions.extend(test_suggestions)
    new_t_suggs, stats = prune_equivalent_popular_codes(mk_regression_tests(test_w_code),
                                    threshold=(len(code_suggestions) * top_rare / 100))
    new_test_suggestions.extend(new_t_suggs)
    return prune_equivalent_codes(new_test_suggestions), stats
