# TiCoder: Test-driven Interactive Code Generation

TiCoder is a workflow for python code generation that allows you to interactively leverage lightweight user feedback to (a) formalize user intent using generated tests that can be useful for debugging, and (b) produce an improved set of code suggestions by pruning and ranking candidate code suggestions. 

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Authenticating with OAI](#authenticating-with-openai-or-azure)

    2.1 [OpenAI API](#openai-api)

    2.2 [Azure OpenAI](#azure-openai)
---
4. [Basic Usage](#running-a-single-example)
5. [Benchmarking](#benchmarking)
6. [Command-Line Options](#command-line-arguments)
---
7. [Citing this work](#citing-this-work)
8. [Contributing](#contributing)
9. [Trademarks](#trademarks)
10. [License](#license)

---

## Installation and Setup

Currently, we have tested the setup on Linux Ubuntu machine. Support for Windows coming soon!

1. **Clone this repository** 
    ```
    git clone https://github.com/microsoft/TiCoder.git
    ```

2. **Create and activate a virtual environment** (Python 3.9 is recommended):
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   cd src
   pip install -r requirements.txt
   ```

---

## Authenticating with OpenAI or Azure

### OpenAI API
Make sure you have a valid OpenAI API Key. You can retrieve it from [OpenAI API Keys](https://platform.openai.com/account/api-keys).

Then, set the environment variable:
```bash
export OPENAI_API_KEY=<your_openai_api_key>
```
If you plan to use Azure OpenAI, you can can keep this variable empty. 

### Azure OpenAI
Azure OpenAI endpoints via OAuth authentication are supported, make sure to run `az login` before trying to run TiCoder. Authentication via API keys are not currently supported. If you are using Azure OpenAI, make sure you have a `configs/azure.json` file with the following structure:

```json
{
    "scope": "<YOUR_AZURE_API_SCOPE>",
    "endpoint": "<YOUR_AZURE_ENDPOINT>",
    "api_version": "<AZURE_OPENAI_API_VERSION>" 
}
```

Then, make sure to run TiCoder with `--use_azure --azure_config configs/azure.json`.

---
## Interaction Modes

TiCODER can be run in two main user-interaction modes, 1) with a user providing feedback on tests from the command line, and 2) simulating the user by using the execution outcome of a ground truth solution to benchmark TiCODER on a large number tasks. In both modes the feedback can be a) an indication if a test should pass/fail or b) provide the correct test output if a test should fail.

## Running a Single Example

### Real-time User Feedback
This mode is intended for an actual human user to respond to queries.

1. Prepare your dataset file (e.g., `../datasets/mbpp/toy.jsonl` for a single example).
2. Run:
   ```bash
   python3 main.py \
       --data_file_path ../datasets/mbpp/toy.jsonl \
       --max_code_suggestions 5 \
       --fix_num_tests 20 \
       --model "gpt-35-turbo_1106" \
       --verbosity 1
   ```
  or if using the Azure Open AI API:
   ```bash
   python3 main.py \
       --data_file_path ../datasets/mbpp/toy.jsonl \
       --max_code_suggestions 5 \
       --fix_num_tests 20 \
       --model "gpt-35-turbo_1106" \
       --use_azure \
       --azure_config configs/azure.json \
       --verbosity 1
   ```
 

### Simulating a User
If you want to simulate a user’s responses automatically, include `--query_oracle` to indicate you’re simulating user feedback by querying the “oracle” (the ground truth). Remove this flag to get actual user feedback.

---

## Benchmarking

### Running TiCODER on MBPP
For example, run on 10 random MBPP examples while querying the reference oracle (simulated user). For each example, 5 code suggestions are generated, and 10 tests are generated per code suggestion:
```bash
python3 main.py \
  --data_file_path ../datasets/mbpp/mbpp.jsonl \
  --query_oracle \
  --max_code_suggestions 5 \
  --verbosity 1 \
  --max_num_examples 10 \
  --fix_num_tests 10 \
  --output_tag <foo>
```
This produces a file `global_results<foo>.json` which logs all results. To run on the full MBPP dataset, drop the `--max_num_examples` flag.

### Gathering Metrics
Use the following to gather metrics from `global_results<foo>.json`:
```bash
python3 analyze_data.py global_results<foo>.json
```
This will return a summary of the results, including the pass@k values at each simulated user interaction. 

### Using a Cache
You can also store code and test generation results in a cache and pass this to TiCODER to test how various code and test pruning parameters impact performance.   

```bash
python3 main.py \
  --data_file_path ../datasets/mbpp/toy.jsonl \
  --max_code_suggestions 20 \
  --fix_num_tests 10 \
  --single \
  --model "gpt-4-0613" \
  --use_dyn \
  --use_opt \
  --codex_cache ./mbpp_gpt4_cache.json \
  --update \
  --query_oracle \
  --max_num_examples 5
```
- `--codex_cache ./mbpp_gpt4_cache.json` points to the cache file.
- `--update` updates the cache if new queries appear.

### Full MBPP Run Examples

1. **Subset of MBPP (10 examples):**
   ```bash
   nohup python3 main.py \
     --data_file_path ../datasets/mbpp/mbpp.jsonl \
     --max_num_examples 10 \
     --max_code_suggestions 100 \
     --fix_num_tests 50 \
     --single \
     --model "gpt-4-0613" \
     --codex_cache ./mbpp_gpt4.json \
     --update \
     --query_oracle \
     --max_user_queries 5 \
     --cluster_ \
     --output_tag foo \
     > mbpp.foo 2>&1 &
   ```

2. **Entire MBPP dataset:**
   ```bash
   nohup python3 main.py \
     --data_file_path ../datasets/mbpp/mbpp.jsonl \
     --max_code_suggestions 100 \
     --fix_num_tests 50 \
     --single \
     --model "gpt-4-0613" \
     --codex_cache ./mbpp_gpt4.json \
     --update \
     --query_oracle \
     --max_user_queries 5 \
     --cluster_ \
     --output_tag foo \
     > mbpp.foo 2>&1 &
   ```
---

## Command-Line Arguments

Below is a summary of the most commonly used arguments in `main.py`. You can see all available arguments in the source code or by running `python main.py --help`.

- **`--sleep_time`** *(int, default=3)*  
  Sleep time in seconds between each example.

- **`--verbosity`** *(int, default=0)*  
  Verbosity level of console output (0=quiet, 1=normal, 2=debug).

- **`--output_tag`** *(str, default='')*  
  Tag to append to output files (e.g., `global_results<tag>.json`).

- **`--codex_cache_file_path`** *(str)*  
  File path to a JSON cache of query-response pairs.  

- **`--update`** *(flag)*  
  Update the cache file with any new queries.

### Example Selection
- **`--data_file_path`** *(str, required)*  
  Path to the JSONL dataset file, where each line is one example.

- **`--function_name`** *(str, default='')*  
  Only run on examples with this function name (filtering).

- **`--max_num_examples`** *(int, default=1000000000)*  
  Maximum number of examples to process.

- **`--min_indx`** *(int, default=0)*  
  Minimum example index to start from (in the JSONL file).

- **`--max_indx`** *(int, default=1000000)*  
  Maximum example index to process.

### User or Oracle Interaction
- **`--query_oracle`** *(flag)*  
  Use the reference oracle (ground truth) instead of a human user.

### Code Generation Options
- **`--sampling_temperature`** *(float, default=0.8)*  
  Temperature for model sampling (higher = more random).

- **`--max_code_suggestions`** *(int, default=10)*  
  Maximum number of code suggestions to generate per query.

- **`--fix_num_tests`** *(int, default=-1)*  
  Number of tests to generate per query.

- **`--rank_test_option`** *(str, default=None)*  
  How to rank generated tests (e.g., `distinguishing`, `random`, `ideal`).

- **`--rank_code_option`** *(str, default=None)*  
  How to rank the generated code suggestions (e.g., `passing_tests`, `weighted`).

- **`--use_validation_tests_in_prompt`** *(flag)*  
  Include validation tests included in the benchmark in the code and test generation prompt.

- **`--regen_code_with_tests_in_prompt`** *(flag)*  
  Regenerate code suggestions by including previously approved tests in the prompt.

- **`--use_dynamic_test_pruning`** *(flag)*  
  Dynamically prune tests using the code suggestions.

- **`--single_assert_per_test`** *(flag)*  
  Generate tests with a single assertion each.

- **`--split_asserts`** *(flag)*  
  Split multi-assert tests into individual single-assert tests.

- **`--multiple_asserts_choice`** *(str, default='top1')*  
  Strategy for selecting among multiple asserts in a single test.

### User Interaction and Queries
- **`--baseline_test_gen_codex`** *(flag)*  
  Use the top-1 generated test with no pruning or filtering.

- **`--user_fixes_tests`** *(flag)*  
  Simulate a scenario where a user corrects a test if it does not align with the intended function behavior. This is currently only supported in benchmarking mode (--query_oracle) and must be used with single_assert tests (e.g. `--single`).

- **`--max_user_queries`** *(int, default=1)*  
  Maximum number of times the user/oracle should be queried for test feedback.

- **`--count_accepted_queries_only`** *(flag)*  
  Only count queries that the user/oracle “accepts” towards the `--max_user_queries`.

- **`--oracle_as_code_suggestion`** *(flag)*  
  Include the oracle’s solution as one of the code suggestions (useful for upper-bound tests).

### Regression & Clustering
- **`--gen_regression_tests`** *(flag)*  
  Generate regression tests from code suggestions that fail.

- **`--cluster_regression_tests`** *(flag)*  
  Cluster test sets based on similarities in failure patterns.

### Model Configuration
- **`--model`** *(str, default='code-davinci-002')*  
  Codex/LLM engine to be used (e.g.: `"gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k-0613", "gpt-4-0314",
        "gpt-4-32k-0314", "gpt-4-0613", "gpt-4-32k-0613"`)  

- **`--max_tokens`** *(int, default=150)*  
  Maximum tokens for each code generation prompt.

- **`--use_azure`** *(flag)*  
  Use the Azure variant of the ChatCompletion API.

- **`--azure_config`** *(str, default='configs/azure.json')*  
  Path to the Azure configuration JSON file.

- **`--token_per_minute_limit`** *(int, default=10000)*  
  Throttle or limit usage based on tokens per minute for Azure.

### Job Parallelization
- **`-j`, `--jobs`** *(int, default=1)*  
  Number of parallel jobs (use `-1` to utilize all available cores).

---

**Happy coding and experimenting with TiCoder!** If you have any questions or need additional help, please open an issue or contribute to the repository.

---
# Citing this work

- [Interactive code generation via test-driven user-intent formalization](https://arxiv.org/abs/2208.05950)

    ```
    @article{lahiri2022interactive,
    title={Interactive code generation via test-driven user-intent formalization},
    author={Lahiri, Shuvendu K and Fakhoury, Sarah and Naik, Aaditya and Sakkas, Georgios and Chakraborty, Saikat and Musuvathi, Madanlal and Choudhury, Piali and von Veh, Curtis and Inala, Jeevana Priya and Wang, Chenglong and others},
    journal={arXiv preprint arXiv:2208.05950},
    year={2022}
    }
    ```

- [LLM-based test-driven interactive code generation: User study and empirical evaluation](https://ieeexplore.ieee.org/abstract/document/10606356/)
    ```
    @article{fakhoury2024llm,
    title={Llm-based test-driven interactive code generation: User study and empirical evaluation},
    author={Fakhoury, Sarah and Naik, Aaditya and Sakkas, Georgios and Chakraborty, Saikat and Lahiri, Shuvendu K},
    journal={IEEE Transactions on Software Engineering},
    year={2024},
    publisher={IEEE}
    }
    ```

---

# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

---

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
