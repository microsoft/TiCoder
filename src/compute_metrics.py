import json
import sys
import numpy as np


def open_json_file(json_file):
    """
    Open and read a json file
    """
    with open(json_file) as json_data:
        data = json.load(json_data)
    return data


def pass_at_k(n, c, k):
    """
    :param n: total number of samples
    :param c: number of correct samples
    :param k: k in pass@$k$
    """
    if n == 0:
        return 0.0
    if c == 0 and n < k:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


if __name__ == "__main__":
    # get the command line arguments using sys.argv
    data = list(filter(lambda d: d is not None, open_json_file(sys.argv[1])))
    # augment the data with the number of unique values

    # number of elements in data results
    if (len(data) == 0):
        print("No data found")
        exit(1)

    print(f"Total number of examples = {len(data)}")
    print("=" * 60)

    for mq in range(len(data[0]['results'])):
        # create a list of k elements initialized to 0
        pass_at_1_lst = []
        pass_at_2_lst = []
        pass_at_5_lst = []
        pass_at_10_lst = []
        pass_at_100_lst = []
        pruned_pass_at_1_lst = []
        pruned_pass_at_2_lst = []
        pruned_pass_at_5_lst = []
        pruned_pass_at_10_lst = []
        pruned_pass_at_100_lst = []
        full_pass_at_1_lst = []
        full_pass_at_2_lst = []
        full_pass_at_10_lst = []
        full_pass_at_100_lst = []
       
        num_corr_sugg = []
        num_top1_corr_sugg = []
        num_top3_corr_sugg = []
        num_top5_corr_sugg = []
        num_top10_corr_sugg = []

        num_top2_corr_sugg = []
        num_top4_corr_sugg = []
        num_top8_corr_sugg = []
        num_top16_corr_sugg = []
        num_top32_corr_sugg = []
        num_top64_corr_sugg = []

        num_suggs = []
        num_one_correct = []
        num_queries = []
        num_pos_tests = []
        num_neg_tests = []

        num_inc_sugg = []
        num_least_one_pos_test = [] # number of data with at least one positive test
        num_least_one_runnable_test = [] # number of data with at least one test that passes or fails an assertion

        num_queries_for_succeeding_test = []

        num_least_one_post_test_first_correct = [] # number of data with least one positive test and first correct suggestion
        num_least_one_runnable_test_first_correct = [] # number of data with at least one test that passes or fails an assertion and first correct suggestion

        examples_with_at_least_1_correct_code = []
        examples_with_at_least_1_correct_test = []
        for d in data:
            if not d['results']:
                continue
            elif mq >= len(d['results']):
                continue
            results = d['results'][mq]
            # number of tests
            num_tests = results['num_tests']
            # number of suggestions by # tests
            num_suggestions = len(results['status'])
            weighted_num_suggestions = 1
            if 'weights' in results:
                weighted_num_suggestions = np.sum(results['weights'])
            # fraction of correct suggestions/total suggestions # tests
            correct_suggestions = len([x for x in results['status'] if x])
            weighted_correct_suggestions = 1
            if 'weights' in results:
                weighted_correct_suggestions = np.sum([x[1] for x in zip(results['status'], results['weights']) if x[0]])
            # fraction of incorrect suggestions/total suggestions # tests
            incorrect_suggestions = len([x for x in results['status'] if not x])
            # position of first-correct suggestion # test
            first_correct_suggestion = results['status'].index(True) if True in results['status'] else -1
            pass_at_1 = pass_at_k(num_suggestions, correct_suggestions, min(1, num_suggestions))
            pass_at_5 = pass_at_k(num_suggestions, correct_suggestions, min(5, num_suggestions))
            pass_at_2 = pass_at_k(num_suggestions, correct_suggestions, min(2, num_suggestions))
            pass_at_10 = pass_at_k(num_suggestions, correct_suggestions, min(10, num_suggestions))
            pass_at_100 = pass_at_k(num_suggestions, correct_suggestions, num_suggestions)
            # number of ways we can sample from 100 - m code suggestions, where m is the number of user pruned code suggestions
            pruned_pass_at_1 = pass_at_k(weighted_num_suggestions, weighted_correct_suggestions, min(1, weighted_num_suggestions))
            pruned_pass_at_2 = pass_at_k(weighted_num_suggestions, weighted_correct_suggestions, min(2, weighted_num_suggestions))
            pruned_pass_at_5 = pass_at_k(weighted_num_suggestions, weighted_correct_suggestions, min(5, weighted_num_suggestions))
            pruned_pass_at_10 = pass_at_k(weighted_num_suggestions, weighted_correct_suggestions, min(10, weighted_num_suggestions))
            pruned_pass_at_100 = pass_at_k(weighted_num_suggestions, weighted_correct_suggestions, weighted_num_suggestions)
       
          
            # numebr of user queries
            num_user_queries = results['num_queries']
            num_pos_user_queries = results['num_pos_tests']
            num_neg_user_queries = results['num_neg_tests']


            num_suggs.append(num_suggestions)
            num_corr_sugg.append(correct_suggestions)
            pass_at_1_lst.append(pass_at_1)
            pass_at_2_lst.append(pass_at_2)
            pass_at_5_lst.append(pass_at_5)
            pass_at_10_lst.append(pass_at_10)
            pass_at_100_lst.append(pass_at_100)
            pruned_pass_at_1_lst.append(pruned_pass_at_1)
            pruned_pass_at_2_lst.append(pruned_pass_at_2)
            pruned_pass_at_5_lst.append(pruned_pass_at_5)
            pruned_pass_at_10_lst.append(pruned_pass_at_10)
            pruned_pass_at_100_lst.append(pruned_pass_at_100)
      

            num_top1_corr_sugg.append(1 if first_correct_suggestion == 0 else 0)
            num_top3_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 3) else 0)
            num_top5_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 5) else 0)
            num_top10_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 10) else 0)
            num_top2_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 2) else 0)
            num_top4_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 4) else 0)
            num_top8_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 8) else 0)
            num_top16_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 16) else 0)
            num_top32_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 32) else 0)
            num_top64_corr_sugg.append(1 if (first_correct_suggestion >= 0 and first_correct_suggestion < 64) else 0)

            num_one_correct.append(1 if correct_suggestions > 0 else 0)
            num_queries.append(num_user_queries)
            num_pos_tests.append(num_pos_user_queries)
            num_neg_tests.append(num_neg_user_queries)
            num_inc_sugg.append(incorrect_suggestions)
            num_queries_for_succeeding_test.append(num_user_queries if num_pos_user_queries > 0 else 0)
            num_least_one_pos_test.append(1 if num_pos_user_queries > 0 else 0)
            num_least_one_runnable_test.append(1 if num_pos_user_queries + num_neg_user_queries > 0 else 0)
            # completely generated by CP!!
            num_least_one_post_test_first_correct.append(1 if first_correct_suggestion == 0 and num_pos_user_queries > 0 else 0)
            num_least_one_runnable_test_first_correct.append(1 if first_correct_suggestion == 0 and (num_pos_user_queries + num_neg_user_queries) > 0 else 0)

        print("-" * 60)
        print(f"Num. of user queries = {num_user_queries}")
        print("-" * 60)

        print(f"top-1 suggs   = {np.mean(num_top1_corr_sugg) * 100.0} %,\t({np.sum(num_top1_corr_sugg)})")
        print(f"top-2 suggs   = {np.mean(num_top2_corr_sugg) * 100.0} %,\t({np.sum(num_top2_corr_sugg)})")
        print(f"top-3 suggs   = {np.mean(num_top3_corr_sugg) * 100.0} %,\t({np.sum(num_top3_corr_sugg)})")
        print(f"top-4 suggs   = {np.mean(num_top4_corr_sugg) * 100.0} %,\t({np.sum(num_top4_corr_sugg)})")
        print(f"top-5 suggs   = {np.mean(num_top5_corr_sugg) * 100.0} %,\t({np.sum(num_top5_corr_sugg)})")
        print(f"top-8 suggs   = {np.mean(num_top8_corr_sugg) * 100.0} %,\t({np.sum(num_top8_corr_sugg)})")
        print(f"top-10 suggs  = {np.mean(num_top10_corr_sugg) * 100.0} %,\t({np.sum(num_top10_corr_sugg)})")
        print(f"top-16 suggs  = {np.mean(num_top16_corr_sugg) * 100.0} %,\t({np.sum(num_top16_corr_sugg)})")
        print(f"top-32 suggs  = {np.mean(num_top32_corr_sugg) * 100.0} %,\t({np.sum(num_top32_corr_sugg)})")
        print(f"top-64 suggs  = {np.mean(num_top64_corr_sugg) * 100.0} %,\t({np.sum(num_top64_corr_sugg)})")
        print(f"top-100 suggs = {np.mean(num_one_correct) * 100.0} %,\t({np.sum(num_one_correct)})")
        print()

        print(f"number of correct suggs   = {np.sum(num_corr_sugg)}")
        print(f"number of incorrect suggs = {np.sum(num_inc_sugg)}")
        print(f"at least one correct = {np.mean(num_one_correct) * 100.0} %, ({np.sum(num_one_correct)})")
        print(f"avg number of correct suggs = {np.mean(num_corr_sugg)}")
        print()

        print(f"pass@1   = {np.mean(pass_at_1_lst) * 100.0} %")
        print(f"pass@2   = {np.mean(pass_at_2_lst) * 100.0} %")
        print(f"pass@5   = {np.mean(pass_at_5_lst) * 100.0} %")
        print(f"pass@10  = {np.mean(pass_at_10_lst) * 100.0} %")
        print(f"pass@100 = {np.mean(pass_at_100_lst) * 100.0} %")
        print(f"pass@1_exists_solution = {np.mean([n[0] for n in zip(pass_at_1_lst, num_one_correct) if n[1] > 0]) * 100.0} %")
        print()

        print(f"pruned pass@1   = {np.mean(pruned_pass_at_1_lst) * 100.0} %")
        print(f"pruned pass@2   = {np.mean(pruned_pass_at_2_lst) * 100.0} %")
        print(f"pruned pass@5   = {np.mean(pruned_pass_at_5_lst) * 100.0} %")
        print(f"pruned pass@10  = {np.mean(pruned_pass_at_10_lst) * 100.0} %")
        print(f"pruned pass@100 = {np.mean(pruned_pass_at_100_lst) * 100.0} %")
        print()
