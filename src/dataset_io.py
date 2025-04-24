import json
import re

import config
from config import debug_print


def create_validation_tests(test_bodies, func_name):
    """Create validation tests"""
    return [
        "def " + config.TEST_PREFIX + func_name + "():\n\t" + test_body
        for test_body in test_bodies
    ]


def read_json_or_jsonl_to_list(file_path):
    if file_path.endswith(".jsonl"):
        with open(file_path, "r") as f:
            return [json.loads(line) for line in f]
    else:
        with open(file_path, "r") as f:
            return json.load(f)


def parse_func_code(data):
    """Extract func name and signature from code"""
    # find all def statements and arguments
    def_stmts = re.findall(r".*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", data["code"])
    def_stmts = dict.fromkeys(def_stmts)
    num = len(def_stmts)
    func_name = None

    if "test_list" in data:
        test_functions = str(data["test_list"])
        for stmt in def_stmts.keys():
            if test_functions.find(stmt) != -1:
                if func_name is None:
                    func_name = stmt
                else:
                    assert (
                        False
                    ), f"Multiple functions under test: {func_name} and {stmt}"
    else:
        func_name = def_stmts[num - 1]

    args = re.findall(r".*def\s+" + func_name + r"(\s*\(.*\)\s*):", data["code"])
    func_sig = args[0] if len(args) > 0 else ""
    return func_name, func_sig


def get_func_details(data):
    # check if data has code_func key
    if "code_func" in data:
        func_name = data["code_func"]
        func_sig = data["code_sig"]
        oracle_body = data["code_body"]
        oracle = "def " + func_name + func_sig + ":" + oracle_body
    else:
        # create name/sig/oracle from code directly
        func_name, func_sig = parse_func_code(data)
        oracle = data["code"]
        print(f"func_name = {func_name}, func_sig = {func_sig}")
    return func_name, func_sig, oracle


def parse_human_eval_data(data):
    prog_data = {}
    sig = data["prompt"]

    prog_data["ctxt"] = ""
    prog_data["sig"] = sig
    prog_data["func_name"] = data["entry_point"]
    prog_data["val_tests"] = [data["test"]]
    prog_data["oracle"] = sig + data["canonical_solution"]
    return prog_data


def parse_mbpp_data(data):
    prog_data = {}
    func_docstring = data["text"]
    func_name, func_sig, oracle = get_func_details(data)
    debug_print(f'"""{func_docstring}"""')
    assert len(data["code"].split("def " + func_name + func_sig + ":")) > 1

    prog_data["ctxt"] = data["code"].split("def " + func_name + func_sig + ":")[0]
    prog_data["sig"] = (
        "def " + func_name + func_sig + ':\n\t"""' + func_docstring + '"""'
    )
    prog_data["func_name"] = func_name
    prog_data["val_tests"] = create_validation_tests(data["test_list"], func_name)
    prog_data["oracle"] = oracle
    return prog_data


def parse_sanitized_mbpp_data(data):
    prog_data = {}
    func_docstring = data["prompt"]
    func_name, func_sig, oracle = get_func_details(data)
    debug_print(f'"""{func_docstring}"""')
    assert len(data["code"].split("def " + func_name + func_sig + ":")) > 1

    prog_data["ctxt"] = data["code"].split("def " + func_name + func_sig + ":")[0]
    prog_data["sig"] = (
        "def " + func_name + func_sig + ':\n\t"""' + func_docstring + '"""'
    )
    prog_data["func_name"] = func_name
    prog_data["val_tests"] = create_validation_tests(data["test_list"], func_name)
    prog_data["oracle"] = oracle
    return prog_data
