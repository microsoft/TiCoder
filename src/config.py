import os
import sys
import time
import openai
import threading
import tiktoken


class TokenCounter:
    def __init__(self, token_limit):
        self.token_limit = token_limit
        self.used_tokens = 0
        self.running = False
        self.thread = None
        self.start()

    def add_tokens(self, num_tokens):
        self.used_tokens += num_tokens

    def reset_token_count(self):
        while self.running:
            time.sleep(60)
            self.used_tokens = 0

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.reset_token_count)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def is_over_limit(self, tentative_tokens=0):
        return self.used_tokens + tentative_tokens > self.token_limit


def count_tokens(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k-0613", "gpt-4-0314",
        "gpt-4-32k-0314", "gpt-4-0613", "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model or "gpt-35" in model:
        print("Warning: gpt-3.5-turbo may update over time. Using token limit assuming gpt-3.5-turbo-0613.")
        return count_tokens(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print(
            "Warning: gpt-4 may update over time. Using token limit assuming gpt-4-0613.")
        return count_tokens(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. "
            "See https://github.com/openai/openai-python/blob/main/chatml.md "
            "for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    if isinstance(messages, str):
        num_tokens += len(encoding.encode(messages))
    else:
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


# Global variables
TEST_PREFIX = 'test_'
test_gen_option = 'pass'
multiple_asserts_choice = 'top1'
single_assert_per_test = True
split_asserts = False
use_validation_tests_in_context = False
rank_test_option = None
rank_code_option = None
skip_codex_query_cnt = 0
mk_codex_query_cnt = 0
cluster_regression_tests = False
count_accepted_queries_only = False
regenerate_code_with_tests_in_prompt = False
use_rare_assert_rewrites = -1
query_oracle_opt = False
use_oracle_as_code_suggestion = False
codex_query_response_log = {}
codex_cache_file = None
max_user_queries = 1
verbosity = 0
dataset_prefix = ''
token_per_minute_limit = 10000

# OpenAI key
OPENAI_API_KEY = 'OPENAI_API_KEY'
if OPENAI_API_KEY not in os.environ:
    print("Please set the environment variable OPENAI_API_KEY")
    sys.exit(1)

# Model parameters
sampling_temperature = 0.8  # default
MAX_TOKENS = 300
TOP_P = 0.95
MODEL = 'gpt-4-0613'
NUM_CODEX_RETRIES = 20
MAX_NUM_CODEX_CODE_SUGGESTIONS = 10
MAX_NUM_CODEX_TEST_SUGGESTIONS = 10


# Utils
def debug_print(string):
    if verbosity > 0:
        print(string)
