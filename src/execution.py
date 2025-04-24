import faulthandler
import signal
import sys
import time
import traceback
from contextlib import redirect_stdout
from io import StringIO
from random import random

from pyext import RuntimeModule

import config
from config import debug_print


# setting up signal timer
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException


def execute_code(code, test, func_name=None):
    # invariant: only one test must be executed
    # assert isinstance(test, (list, tuple)) and len(test) == 1
    # only one test from now on

    signal.signal(signal.SIGALRM, timeout_handler)
    timeout = 1  # seconds

    sol = "import sys\nimport time\nimport itertools\nfrom itertools import accumulate, product, permutations, combinations\nimport collections\nfrom collections import Counter, OrderedDict, deque, defaultdict, ChainMap\nfrom functools import lru_cache\nimport math\nfrom math import sqrt, sin, cos, tan, ceil, fabs, floor, gcd, exp, log, log2\nimport fractions\nfrom typing import List, Tuple\nimport numpy as np\nimport random\nimport heapq\nfrom heapq import *\n"
    sol += code
    sol += "\n"
    sol += test
    if config.dataset_prefix == "humaneval" and "check" in test:
        sol += "\n"
        sol += f"check({func_name})"
    else:
        sol += "\n"
        sol += f"{config.TEST_PREFIX + func_name}()"
    try:
        debug_print(f"Executing {sol}")
        signal.alarm(timeout)
        faulthandler.enable()
        with redirect_stdout(StringIO()):
            RuntimeModule.from_string(f"tmp_sol_{time.time_ns()}_{random()}", sol)
    except Exception as e:
        signal.alarm(0)
        debug_print(f"error = {e}")
        raise e

    signal.alarm(0)
    debug_print("PASS")
    return "PASSED"


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


def test_code(test, code, func_name=None):
    """Run the the python code test and return True if it succeeds"""
    # Invariant: number of tests == 1 and tests can either be a list or a tuple
    # assert isinstance(tests, (list, tuple)) and len(tests) == 1
    # Give only one test from now on

    with timeout(seconds=1):
        try:
           
            res = execute_code(code, test, func_name)
            debug_print("Tests passed")
            if res == "PASSED":
                return (True, None)
            else:
                assert False, f"Result is {res}"
        except TimeoutError:
            debug_print("Test failed due to timeout")
            return (False, TimeoutError)
        except SystemExit as e:
            debug_print(f"Test failed due to SystemExit {e}")
            return (False, str(e))
        except Exception as e:
            if isinstance(e, AssertionError):
                debug_print("Test failed due to assertion error")
                return (False, AssertionError)
            if config.verbosity > 0:
                traceback.print_exc()
            debug_print("Error in code or test failed")
            return (False, None)
        except:
            info = sys.exc_info()[0]
            descr = sys.exc_info()[1]
            debug_print (f"Unexpected exception while execution {info} {descr}")
            return (False, None)


def satisfies_validation_tests(code, prog_data):
    """Check if code passes all the validation tests"""
    for test in prog_data['val_tests']:
        if not test_code(test, code, prog_data['func_name'])[0]:
            return False
    return True
