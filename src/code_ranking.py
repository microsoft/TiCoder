from math import sqrt

from execution import test_code


def rerank_codes(codes, tests, rank_code_option, func_name=None):
    if rank_code_option is None:
        return codes

    if rank_code_option == "passing_tests":
        return rank_codes_by_passing_tests(codes, tests, func_name)

    if rank_code_option == "weighted":
        return rank_codes_by_weighted_passing_tests(codes, tests, func_name)

    if rank_code_option == "code_t":
        return rank_codes_by_dual_execution_agreement(codes, tests, func_name)

    raise NotImplementedError


def rank_codes_by_passing_tests(codes, tests, func_name):
    """Rank codes based on the number of tests they pass"""
    passed_tests = {}
    for code in codes:
        passed_tests[code] = len(list(filter(lambda t: test_code(t, code, func_name)[0], tests)))
    codes = sorted(codes, key=passed_tests.get, reverse=True)
    return codes


def rank_codes_by_weighted_passing_tests(codes, tests, func_name):
    """Rank codes based on the number of tests they pass
       When a test passes more codes though, it contributes less to the overall code score"""
    test_stats = {}
    passed_tests = {}
    for test in tests:
        test_stats[test] = 0
        for code in codes:
            if test_code(test, code, func_name)[0]:
                passed_tests[code].append(test)
                test_stats[test] += 1
    for code in codes:
        score = 0
        for test in tests:
            if test in passed_tests[code]:
                score += 100.0 / test_stats[test]
        passed_tests[code] = score
    codes = sorted(codes, key=passed_tests.get, reverse=True)
    return codes


def rank_codes_by_dual_execution_agreement(codes, tests, func_name):
    """Rank codes based on the dual execution agreement,
       introduced at CodeT paper [Chen et al. 2022]"""
    code_clusters = {} # {set of test ids} => code cluster list
    for code in codes:
        test_ids = []
        for idx, test in enumerate(tests):
            if test_code(test, code, func_name)[0]:
                test_ids.append(idx)
       
        if len(test_ids) == 0:
            return codes
            
        test_ids = tuple(sorted(test_ids))
        code_clusters[test_ids].append(code)

    g_test_score = 1 / len(tests)
    f_cluster_scores = {} # {set of test ids} => code cluster f-score
    for test_id, cluster in code_clusters.items():
        f_cluster_scores[test_id] = sqrt(len(cluster)) * len(test_id) * g_test_score
   
    ranked_cluster_keys = sorted(code_clusters.keys(), key=f_cluster_scores.get, reverse=True)
    codes = [code_clusters[key][0] for key in ranked_cluster_keys]
    # This will also prune codes, since codes that pass the same tests are in the same cluster
    # and we return only the first code in the cluster
    return codes
