import code_ranking as cr
import config
import test_ranking as tr
from config import debug_print
from execution import satisfies_validation_tests, test_code
from assertion_rewriter import rewrite_assert

def query_user(test):
    """Query user for approval of test"""
    return input(f"Test ** \n {test}\n Do you approve this test? (y/n) Press enter to skip:")


def query_oracle(test, prog_data):
    """Query an oracle to check if it satisfies the test"""
    result = test_code(test, prog_data['oracle'], prog_data['func_name'])
    if result[0]:
        return 'y'
    elif result[1] == AssertionError:
        return 'n'
    else:
        return 'skip'


def query_user_or_oracle(test, prog_data):
    debug_print(f"query_oracle_opt = {config.query_oracle_opt}")
    if config.query_oracle_opt:
        return query_oracle(test, prog_data)
    else:
        return query_user(test)


def satisfies_hidden_validation_tests_when_query_oracle(code, prog_data):
    """Check if code satisfies hidden validation tests when query oracle"""
    if config.query_oracle_opt:
        return satisfies_validation_tests(code, prog_data)
    else:
        return False


def prune_codes_that_dont_pass_test(test, codes, prog_data):
    # don't prune if a code satisfies hidden validation tests
    return [code for code in codes if (satisfies_hidden_validation_tests_when_query_oracle(code, prog_data) or test_code(test, code, prog_data['func_name'])[0])]


def prune_codes_that_pass_test(test, codes, prog_data):
    # don't prune if a code satisfies hidden validation tests
    return [code for code in codes if (satisfies_hidden_validation_tests_when_query_oracle(code, prog_data) or not test_code(test, code, prog_data['func_name'])[0])]


def prune_code_test_using_user_query(codes, tests, prog_data):
    approved_tests = set()
    rejected_tests = set()
    num_user_queries = 0

    results = []

    if len(tests) == 0 and config.max_user_queries == 0:
        results.append((num_user_queries, codes, list(approved_tests), list(rejected_tests)))
        return results

    orig_codes_len = len(codes)

    while True:
        if len(tests) == 0 or config.max_user_queries <= 0:
            break
        if config.max_user_queries >= 0:
            # if max_user_queries is -1, then we dont prune
            if not config.count_accepted_queries_only and num_user_queries >= config.max_user_queries:
                break
            elif config.count_accepted_queries_only and len(approved_tests) >= config.max_user_queries:
                break
        if num_user_queries >= 10 and config.count_accepted_queries_only:
            break
        # rank the tests based on various criteria
        tests = tr.rerank_tests(tests, codes, config.rank_test_option, prog_data)
        test = tests[0]
        tests = tests[1:] # remove the test from the list
        # user feedback
        ans = query_user_or_oracle(test, prog_data)
        if ans == "y":
            debug_print("Approved test")
            codes = prune_codes_that_dont_pass_test(test, codes, prog_data)
            approved_tests.add(test)
        elif ans == "n":
            debug_print("Rejected test")
            codes = prune_codes_that_pass_test(test, codes, prog_data)
            if config.user_fixes_tests:
                # rewrite the test with assertion rewrite
                if not config.single_assert_per_test:
                    raise Exception("Providing test feedback only works with single_assert_per_test")
                try:
                    fixed_test = rewrite_assert(prog_data['oracle'], test)
                    debug_print(f"rewrote {test} to {fixed_test}")
                    codes = prune_codes_that_dont_pass_test(test, codes, prog_data)
                    approved_tests.add(test)
                except:
                    import traceback
                    debug_print(f"Exception in rewriter: {traceback.format_exc()}")
            else:
                rejected_tests.add(test)
        else:
            debug_print("Skipping test")
        num_user_queries += 1
        codes = cr.rerank_codes(codes, tests, config.rank_code_option, prog_data['func_name'])
        debug_print(f"Remaining codes {len(codes)}/{orig_codes_len}")
        results.append((num_user_queries, codes, list(approved_tests), list(rejected_tests)))
    return results
