import argparse
import concurrent.futures as cf
import json
import os
import random
import sys
import traceback
from multiprocessing import cpu_count
from tqdm import tqdm
import query_chat_model
from pebble import ProcessExpired, ProcessPool
import model_setup
from model_setup import oai_client, aoai_client
import config
import dataset_io as dio
import dynamic_mutation as dm
import dynamic_pruning as dp
import execution as ex
import static_mutation as sm
import user_interaction as ui
from config import debug_print

# Extra global variables
total_tests = 0
valid_tests = 0
valid_test_exists_for_program = 0
total_pruned_tests = 0
valid_pruned_tests = 0
valid_pruned_test_exists_for_program = 0
qm = None
counter = None

def prune_code_using_testgen(prog_data, code_suggestions, num_tests):
    global total_tests, valid_tests, valid_test_exists_for_program, qm
    global total_pruned_tests, valid_pruned_tests, valid_pruned_test_exists_for_program
    global counter
    if counter is None:
        counter = config.TokenCounter(config.token_per_minute_limit)
    # generate tests using testgen
    print('*' * 40  + 'Test Generation' + '*' * 40)
    test_suggestions = qm.get_test_suggestions(client, prog_data, num_tests, code_suggestions, token_counter=counter)
    print('*' * 40  + 'End Test Generation' + '*' * 40)

    # find how many generated tests had assertions
    if num_threads == 1:
        flag = True
        for test in test_suggestions:
            total_tests += 1
            if sm.is_valid_assert_test(test):
                valid_tests += 1
                if flag:
                    valid_test_exists_for_program += 1
                    flag = False

    if not config.baseline_test_gen_codex:
        # prune tests statically (unless we are in the baseline)
        print('*' * 40  + 'Static Pruning' + '*' * 40)
        test_suggestions = sm.prune_tests_statically(test_suggestions)
        print('*' * 40  + 'End Static Pruning' + '*' * 40)
        # split tests and generate more sigle assertions
        if config.split_asserts:
            print('*' * 40  + 'Split Asserts' + '*' * 40)
            test_suggestions = sm.split_tests(test_suggestions)[:100]
            test_suggestions = sm.prune_equivalent_codes(test_suggestions)
            print('*' * 40  + 'End Split Asserts' + '*' * 40)
        # prune tests using code suggestios
        if config.dynamic_test_pruning:
            print('*' * 40  + 'Dynamic Pruning' + '*' * 40)
            test_suggestions = dp.prune_tests_that_dont_pass_code(code_suggestions, test_suggestions, prog_data['func_name'])
            print('*' * 40  + 'End Dynamic Pruning' + '*' * 40)
        # OPTIMISTIC: prune code that doesn't pass any of the tests above
        if config.optimistic_code_pruning and len(test_suggestions) > 0:
            print('*' * 40  + 'Optimistic Pruning' + '*' * 40)
            code_suggestions = dp.prune_codes_that_dont_pass_any_tests(code_suggestions, test_suggestions, prog_data['func_name'])
            print('*' * 40  + 'End Optimistic Pruning' + '*' * 40)

   
    # equivalent tests
    test_suggestions = sm.prune_equivalent_codes(test_suggestions)
    stats = {}

    if config.gen_regression_tests_from_code_suggestions and len(test_suggestions) > 0:
        print('*' * 40  + 'Assert Rewrites' + '*' * 40)
        if config.use_rare_assert_rewrites > 0:
            # pair all tests with all code suggestions and keep only "rare" tests (assert-rewrite-rare)
            test_suggestions = dm.assert_rewrite_rare(code_suggestions, test_suggestions, config.use_rare_assert_rewrites)
        else:
            # pair all tests with all code suggestions (assert-rewrite-all)
            test_suggestions = dm.assert_rewrite_all(code_suggestions, test_suggestions)
        print('*' * 40  + 'End Assert Rewrites' + '*' * 40)

       
    if config.cluster_regression_tests and len(test_suggestions) > 0:
        test_suggestions = dm.cluster_using_regression_tests(code_suggestions, test_suggestions)
        debug_print(f"Clustered tests after regression = {len(test_suggestions)}")

    # find how many pruned tests had assertions
    if num_threads == 1:
        flag = True
        for test in test_suggestions:
            total_pruned_tests += 1
            if sm.is_valid_assert_test(test):
                valid_pruned_tests += 1
                if flag:
                    valid_pruned_test_exists_for_program += 1
                    flag = False

    incorrect_codes_pruned, all_codes = [], []
    if get_pruned_stats_in_global:
        incorrect_codes_pruned, all_codes = get_pruned_bad_codes_for_tests(test_suggestions, code_suggestions, prog_data)

    temp_results = ui.prune_code_test_using_user_query(code_suggestions, test_suggestions, prog_data)
    return temp_results, incorrect_codes_pruned, all_codes, stats #len(test_suggestions)


def get_pruned_bad_codes_for_tests(tests, codes, prog_data):
    """Get the number of (bad) codes each test would prune
       (Greedy ranking statistics)"""
    good_codes = []
    bad_codes = []
    for c in codes:
        if ex.satisfies_validation_tests(c, prog_data):
            good_codes.append(c)
        else:
            bad_codes.append(c)
    total_bad_codes = len(bad_codes)
    total_good_codes = len(good_codes)
    pruned_tests = {}
   
    for test in tests:
        ans = ui.query_oracle(test, prog_data)
        if ans == "y":
            pruned_tests[test] = (total_bad_codes - len(ui.prune_codes_that_dont_pass_test(test, bad_codes, prog_data)), total_good_codes - len(ui.prune_codes_that_dont_pass_test(test, good_codes, prog_data)))
        elif ans == "n":
            pruned_tests[test] = (total_bad_codes - len(ui.prune_codes_that_pass_test(test, bad_codes, prog_data)), total_good_codes - len(ui.prune_codes_that_pass_test(test, good_codes, prog_data)))
        else:
            pruned_tests[test] = (0, 0)
    return pruned_tests, len(codes)


def tappy_entry_func(prog_data, orig_codes, codes, results, n):
    global qm, counter
    if counter is None:
        counter = config.TokenCounter(config.token_per_minute_limit)
    orig_code_len = len(codes)
    print('\n' + '=' * 50  + 'TiCoder' + '=' * 50 + '\n')
    local_results, num_of_pruned_codes_per_test, num_of_codes, stats = prune_code_using_testgen(prog_data, codes, n)
    print('\n' + '=' * 50  + 'End TiCoder' + '=' * 50 + '\n')

    print('=' * 50  + 'Final Results' + '=' * 50)
    for num_queries, codes, tests, neg_tests in local_results:
        print(f">>> Number of User queries = {num_queries}")
        if config.regenerate_code_with_tests_in_prompt and len(tests) > 0:
            orig_codes, codes = qm.gen_and_prune_codes(client, prog_data, tests[:3] if len(tests) > 3 else tests, token_counter=counter)
            orig_code_len = len(codes)
            # we already know the neg_tests and num_queries
            for test in tests:
                codes = ui.prune_codes_that_dont_pass_test(test, codes, prog_data)

        # print final code suggestions
        print(f"Pruned {orig_code_len - len(codes)} / {orig_code_len} codes using test queries")
        debug_print('*' * 40 + 'Pruned Codes' + '*' * 40)
        for code in set(orig_codes) - set(codes):
            debug_print(code)
            debug_print('-' * 80)

        print(f"Final Code suggestions: {len(codes)}")
        print('*' * 40 + 'Final Code Suggestions that are consistent with user-approved tests' + '*' * 40)
        for code in codes:
            print(code)
            print('-' * 80)
        print(f"Final User-Approved Test suggestions: {len(tests)}")
        print('*' * 40 + 'Final User-Approved Test Suggestions' + '*' * 40)
        for test in tests:
            print(test)
            print('-' * 80)
        status  = [ex.satisfies_validation_tests(code, prog_data) for code in codes]
        weights = [orig_codes.count(code) for code in codes]

        local_result = {
                    'num_tests'     : n,
                    'num_queries'   : num_queries,
                    'num_pos_tests' : len(tests),
                    'num_neg_tests' : len(neg_tests),
                    'status'        : status,
                    'weights'       : weights
                }
        if get_pruned_stats_in_global:
            num_of_original_tests_left = 0
            for test in num_of_pruned_codes_per_test:
                fst, snd = num_of_pruned_codes_per_test[test]
                if test in stats:
                    # test was generated from assert-rewrite
                    num_of_pruned_codes_per_test[test] = (fst, snd, stats[test])
                else:
                    # test is from the original codex tests after pruning
                    num_of_pruned_codes_per_test[test] = (fst, snd, -1)
                    num_of_original_tests_left += 1
            local_result['num_of_original_tests_left'] = num_of_original_tests_left
            local_result['num_of_rewritten_tests']     = len(num_of_pruned_codes_per_test) - num_of_original_tests_left
            local_result['num_of_final_codes']         = num_of_codes
            local_result['pruned_codes_per_test']      = num_of_pruned_codes_per_test
        results.append(local_result)
        print()
    print('=' * 50  + 'End Final Results' + '=' * 50)


def append_to_json(file_path, data):
    # append dictionary to an json file
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            json_data.append(data)
    with open(file_path, 'w') as f:
        json.dump(data, f)



def parse_command_line_args():
    parser = argparse.ArgumentParser()
    # options that do not affect the metrics
    parser.add_argument('--sleep_time',              type=int, default=3,  help='Sleep time in seconds between each example')
    parser.add_argument('--verbosity',               type=int, default=0,  help='Verbosity level')
    parser.add_argument('--output_tag',              type=str, default='', help='Tag to append to output files')
    parser.add_argument('--codex_cache_file_path',   type=str,             help='Use a file containing query and response from earlier calls to Codex')
    parser.add_argument('--update_codex_cache_file', action='store_true',  help='Update codex cache file')
    # examples to choose
    parser.add_argument('--data_file_path',   type=str, required=True,      help='Path to a JSONL data file where each line contains a single example')
    parser.add_argument('--function_name',    type=str, default='',         help='Only run on examples matching the function name')
    parser.add_argument('--max_num_examples', type=int, default=1000000000, help='Number of examples to uniform randomly try out from a list of examples')
    parser.add_argument('--min_indx',         type=int, default=0,          help='Minimum index of examples in a JSONL to run')
    parser.add_argument('--max_indx',         type=int, default=1000000,    help='Maximum index of examples in a JSONL to run')
    # for user/simulation
    parser.add_argument('--query_oracle', action='store_true', help='Use provided code oracle instead of querying an user')
    # options
    parser.add_argument('--sampling_temperature',            type=float, default=0.8,  help='Temperature for sampling')
    parser.add_argument('--max_code_suggestions',            type=int, default=10,     help='Maximum number of code suggestions to return')
    parser.add_argument('--fix_num_tests',                   type=int, default=-1,     help='Run test gen to get n tests')
    parser.add_argument('--test_gen_option',                 type=str, default='pass', help='Test gen option {skip, pass, oracle, top1, random, suggestions, ideal}')
    parser.add_argument('--rank_test_option',                type=str, default=None,   help='Rank the tests based on one option {distinguishing, distinguishing_simple, weighted, random, greedy, ideal, failed_codes}')
    parser.add_argument('--rank_code_option',                type=str, default=None,   help='Rank the codes based on one option {passing_tests, weighted, code_t}')    
    parser.add_argument('--use_validation_tests_in_prompt',  action='store_true',      help='Use validation tests in prompt')
    parser.add_argument('--regen_code_with_tests_in_prompt', action='store_true',      help='Regenerate code with approved tests in prompt')
    parser.add_argument('--use_dynamic_test_pruning',        action='store_true',      help='Prune tests using code suggestions')
    parser.add_argument('--use_rare_assert_rewrites',        type=int, default=-1,     help='Use only top-% rare assert-rewrittrn tests')
    parser.add_argument('--use_optimistic_code_pruning',     action='store_true',      help='Prune codes that dont pass the generated tests (can remove correct suggestions)')
    parser.add_argument('--single_assert_per_test',          action='store_true',      help='Use single assert per test')
    parser.add_argument('--split_asserts',                   action='store_true',      help='Use single assert per test by splitting multiple assert tests')
    parser.add_argument('--multiple_asserts_choice',         type=str, default='top1', help='Multiple asserts selection method for single assert tests {top1, random}')
    parser.add_argument('--baseline_test_gen_codex',         action='store_true',      help='Just use the top-1 test from Codex with no static/dynamic pruning or filtering')
    parser.add_argument('--user_fixes_tests',                action='store_true',      help='User responds correctly to a test if it does not satisfy the intent (Assistant #3 in user study)')
    parser.add_argument('--max_user_queries',                type=int, default=1,      help='Maximum number of user queries to ask')
    parser.add_argument('--count_accepted_queries_only',     action='store_true',      help='Only count accepted queries with max_user_queries')
    parser.add_argument('--oracle_as_code_suggestion',       action='store_true',      help='Use oracle as code suggestion for upper bound')
    parser.add_argument('--gen_regression_tests',            action='store_true',      help='Generate regression tests from code suggestions')
    parser.add_argument('--cluster_regression_tests',        action='store_true',      help='Cluster based on regressions tests')
    parser.add_argument('--model',                    type=str, help='Name of the model to be used for inference')
    parser.add_argument('--max_tokens',                      type=int, default=150,    help='Maximum number of tokens for each prompt')
    parser.add_argument('--get_pruned_stats_in_global',      action='store_true',      help='Store pruned test statistics from ideal ranking in global results')
    parser.add_argument('-j', '--jobs',                      type=int, default=1,      help='Number of jobs. Pass -1 for max number of threads')
    parser.add_argument('--test_output',                     default='-',              help='File to store generated tests in')
    parser.add_argument('--pass_at_one',                     action='store_true',      help='Use different settings to get one (good) Codex code suggestion')
    parser.add_argument("--use_azure",                    action='store_true',      help='Use Azure chat model for user interaction')
    parser.add_argument("--azure_config",                 type=str, default='configs/azure.json', help='Azure chat model config file')
    parser.add_argument("--token_per_minute_limit",       type=int, default=10000, help='Token per minute limit for Azure chat model')
    args =  parser.parse_args()
    global qm
    global client

    qm = query_chat_model
    if args.use_azure: 
        client = aoai_client(args.azure_config)
    else:
        client = oai_client()
    return args


if __name__ == "__main__":
    args = parse_command_line_args()
    # print all args including defaults
    print("Command line args with defaults ==>\n\t" + '\n\t'.join([f"--{k}={v}" for k, v in vars(args).items()]))
    data_list = dio.read_json_or_jsonl_to_list(args.data_file_path)
    config.query_oracle_opt = args.query_oracle
    config.test_gen_option = args.test_gen_option
    config.rank_test_option = args.rank_test_option
    config.rank_code_option = args.rank_code_option
    config.gen_regression_tests_from_code_suggestions = args.gen_regression_tests
    config.use_validation_tests_in_context = args.use_validation_tests_in_prompt
    config.regenerate_code_with_tests_in_prompt = args.regen_code_with_tests_in_prompt
    config.single_assert_per_test = args.single_assert_per_test
    config.split_asserts = args.split_asserts
    
    if config.single_assert_per_test:
        config.multiple_asserts_choice = args.multiple_asserts_choice

    config.use_rare_assert_rewrites = args.use_rare_assert_rewrites
    config.codex_cache_file = args.codex_cache_file_path
    config.dynamic_test_pruning = args.use_dynamic_test_pruning
    config.baseline_test_gen_codex = args.baseline_test_gen_codex
    config.optimistic_code_pruning = args.use_optimistic_code_pruning
    config.max_user_queries = args.max_user_queries
    config.count_accepted_queries_only = args.count_accepted_queries_only
    assert args.fix_num_tests >= 5 * args.max_user_queries, "fix_num_tests should be greater than 5 * max_user_queries to ensure that we have enough tests to query after pruning"
    config.use_oracle_as_code_suggestion = args.oracle_as_code_suggestion
    config.cluster_regression_tests = args.cluster_regression_tests
    config.sampling_temperature = args.sampling_temperature
    output_tag = args.output_tag
    config.MODEL = args.model
    config.MAX_TOKENS = args.max_tokens
    num_threads = cpu_count() if args.jobs < 0 else args.jobs
    update_codex_cache_file = args.update_codex_cache_file
    get_pruned_stats_in_global = args.get_pruned_stats_in_global
    config.user_fixes_tests = args.user_fixes_tests

    config.MAX_NUM_CODEX_CODE_SUGGESTIONS = args.max_code_suggestions
    config.token_per_minute_limit = args.token_per_minute_limit
    counter = config.TokenCounter(config.token_per_minute_limit)

    if "mbpp" in args.data_file_path.lower():
        config.dataset_prefix = "mbpp"
    elif "humaneval" in args.data_file_path.lower():
        config.dataset_prefix = "humaneval"

    if args.pass_at_one:
        config.MAX_NUM_CODEX_TEST_SUGGESTIONS = 1
        config.MAX_TOKENS = 300
        config.TOP_P = 0.95
        config.sampling_temperature = 0
        config.max_user_queries = 0

    if args.test_output != "-":
        sys.stdout = open(args.test_output, 'w')

    # Seed for random generator
    random.seed(output_tag)

    print(f"Using Model: {config.MODEL}")

    if args.test_output == "-":
        assert args.jobs == 1, "Must specify an output file using --test_output for multiprocessing support"

    if update_codex_cache_file:
        assert args.jobs == 1, "Update only works in single threaded calls"

    if config.codex_cache_file is not None:
        # only support this for pass option, due to the reason that suggestions/regressions will end up generating 100 tests per code suggestion (for now)
        assert config.test_gen_option == 'pass' or config.test_gen_option == 'top1' or config.test_gen_option == 'random' or config.test_gen_option == 'skip' or config.test_gen_option == 'ideal', "Only support codex cache file for skip, pass, top1 and ideal options"
        if os.path.exists(config.codex_cache_file):
            with open(config.codex_cache_file, 'r') as f:
                config.codex_query_response_log = json.load(f)
        else:
            config.codex_query_response_log = {}
    config.verbosity = args.verbosity
    global_results = []

    def process_data_sample(tup):
        global qm, counter, update_codex_cache_file
        if counter is None:
            counter = config.TokenCounter(config.token_per_minute_limit)
        i, data = tup
        try:
            numtests = args.fix_num_tests
            if args.pass_at_one:
                numtests = 0
            #randomly select the example with probability 1/max_num_examples
            if random.random() > args.max_num_examples/len(data_list):
                debug_print(f"Skipping example {i} due to random sample")
                return

            if "HumanEval" in args.data_file_path:
                prog_data = dio.parse_human_eval_data(data)
            elif "sanitized-mbpp" in args.data_file_path:
                prog_data = dio.parse_sanitized_mbpp_data(data)
            else:
                prog_data = dio.parse_mbpp_data(data)
            debug_print(f"Validations tests: {prog_data['val_tests'][0]}")
            # check if data has function name
            if args.function_name != '' and prog_data['func_name'] != args.function_name:
                debug_print(f"Skipping example {i} due to function name not matched")
                return
            # get the common code suggestions
            tests_in_ctxt = prog_data['val_tests'] if config.use_validation_tests_in_context else None
            print('*' * 40  + 'Code Generation' + '*' * 40)
            orig_codes, codes = qm.gen_and_prune_codes(client, prog_data, tests_in_ctxt, token_counter=counter)
            print('*' * 40  + 'End Code Generation' + '*' * 40)

            # store the results for each example with different number of test steps
            # create a json object with example, num_code_suggestions, and status vector for each test step
            results = []
            tappy_entry_func(prog_data, orig_codes, codes, results, numtests)

            record_i = {
                'func_name': prog_data['func_name'],
                'index': i,
                'num_code_suggestions': len(codes),
                'results': results
            }
            # global_results.append(record_i)
            debug_print(f"Record[i] ==> {record_i}")
            if update_codex_cache_file:
                assert config.codex_cache_file is not None
                with open(config.codex_cache_file, 'w') as f:
                    json.dump(config.codex_query_response_log, f)
            return record_i
        except KeyboardInterrupt as key_err:
            print (f"Exit due to {key_err}")
            raise key_err
        

    data_process_args = [ (i, data) for i, data in enumerate(data_list) if i >= args.min_indx and i <= args.max_indx ]
    if num_threads != 1:
        global_results = []
        with ProcessPool(max_workers=num_threads, max_tasks=5) as pool:
            future = pool.map(process_data_sample, data_process_args, chunksize=1)
            it = future.result()
            while True:
                try:
                    local_results = next(it)
                    global_results.append(local_results)
                except StopIteration:
                    break
                except (cf.TimeoutError, ProcessExpired):
                    continue
                except Exception as e:
                    print(f"Final catastrophic exception {str(e)}")
                    if config.verbosity > 0:
                        traceback.print_tb(e.__traceback__)
                    continue
    else:
        global_results = [process_data_sample(tup) for tup in tqdm(data_process_args)]

    # print the global_results
    debug_print(f"Global results: {global_results}")
    # print the global_results to a json file
    os.makedirs('results', exist_ok=True)
    with open('results/global_results.' + output_tag + '.json', 'w') as f:
        json.dump(global_results, f, indent=4)
    if update_codex_cache_file:
        assert config.codex_cache_file is not None
        with open(config.codex_cache_file, 'w') as f:
            json.dump(config.codex_query_response_log, f)
    # print number of times a query was made and skipped
    if False: #num_threads == 1:
        # FIXME: these globals don't work for multi-thread yet
        print(f"Number of model queries made (skipped) = {config.mk_codex_query_cnt} ({config.skip_codex_query_cnt})")
        if total_tests > 0:
            print(f"Number of valid (assert) tests = {valid_tests}/{total_tests} ({valid_tests * 100 / total_tests:.2f})")
            print(f"Number of programs with a valid (assert) test = {valid_test_exists_for_program}/{len(data_process_args)} ({valid_test_exists_for_program * 100 / len(data_process_args):.2f})")
            if total_pruned_tests > 0:
                print(f"Number of valid pruned (assert) tests = {valid_pruned_tests}/{total_pruned_tests} ({valid_pruned_tests * 100 / total_pruned_tests:.2f})")
            else:
                print(f"Number of valid pruned (assert) tests = {valid_pruned_tests}/{total_pruned_tests}")
            print(f"Number of programs with a valid pruned (assert) test = {valid_pruned_test_exists_for_program}/{len(data_process_args)} ({valid_pruned_test_exists_for_program * 100 / len(data_process_args):.2f})")
    counter.stop()