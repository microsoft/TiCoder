The directory contains the following files:

- *mbpp.jsonl*: The file from the google paper https://arxiv.org/abs/2108.07732 Program Synthesis with Large Language Models
                Each line is a valid JSON element, corresponds to a single example
- *toy.jsonl*: Schema for our tool of simple examples to test the tool ../../src/main.py
               Each line is a valid JSON element, corresponding to a single example
               Since the MBPP json format does not explicitly mention the func_name/signature/prefix/body, we explicitly add them in this format. We will rely on a converter to extract into this from mbpp.jsonl
              