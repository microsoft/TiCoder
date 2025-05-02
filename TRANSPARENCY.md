# TICODER: TEST-DRIVEN INTERACTIVE CODE GENERATION
## OVERVIEW
This work introduces a novel workflow that leverages user-feedback through LLM-generated tests to improve the trust and correctness of LLM-generated code. This workflow of test-driven interactive code generation (TICODER) aims to (a) clarify (i.e., partially formalize) user intent through generated tests, and (b) generate a ranked list of code that is consistent with such tests and return the code and test suggestions to the user. This readme concerns the release of the code that instantiates this workflow, and can be used by users to generate better code and test suggestions, or at scale to benchmark models code generation performance on various datasets. We provide a tool to instantiate this workflow, which includes calls to user-provided LLMs to generate code and tests, and our algorithm for ranking tests and pruning code suggestions.  

## WHAT CAN TICODER DO
TiCocder was developed to help clarify user intent through tests, for the ultimate goal of improving LLM-generated code suggestions. A detailed discussion of TiCoder, including how it was developed and tested, can be found in our paper at: [LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation](https://arxiv.org/abs/2404.10100)

## INTENDED USES
TiCoder is best suited for researchers exploring how to improve code generation techniques via user interaction. TiCoder is being shared with the research community to facilitate reproduction of our results and foster further research in this area. TiCoder is intended to be used by domain experts who are independently capable of evaluating the quality of outputs before acting on them.
Users interact with the tool either by running a script providing a benchmark dataset in automated mode, or via interactive mode in the command line. The interactive mode does not have a UI but requires the user to give feedback on test cases rather than using the gold standard solution provided in the benchmark. 
If running in interactive mode the users provide prompts in a dataset file and then interactively indicate (Y/N) in the terminal if they approve of a test. Users indicate how many of these interaction rounds the tool can request. If running in automated mode, no interaction is requested. 

## OUT-OF-SCOPE USES
TiCoder is not well suited for production systems that intend to bypass sandboxed code execution. 
We do not recommend using TiCoder in commercial or real-world applications without further testing and development. It is being released for research purposes.
TiCoder was not designed or evaluated for all possible downstream purposes. Developers should consider its inherent limitations as they select use cases, and evaluate and mitigate for accuracy, safety, and fairness concerns specific to each intended downstream use.
TiCoder should not be used in highly regulated domains where inaccurate outputs could suggest actions that lead to injury or negatively impact an individual's legal, financial, or life opportunities.
We do not recommend using TiCoder in the context of high-risk decision making (e.g. in law enforcement, legal, finance, or healthcare). 

## HOW TO GET STARTED
To begin using TiCoder, read the paper and follow the instructions on the TiCoder Github repository. 

## EVALUATION
TiCoder was evaluated on its ability to improve code generation accuracy on two benchmarks: MBPP and HumanEval.
A detailed discussion of our evaluation methods and results can be found in our paper at: LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation

## EVALUATION METHODS
We used pass@k to measure TiCoder’s performance.
We compared the performance of TiCoder against direct prompting techniques using MBPP and HumanEval.
We used the following models for benchmarking: 
-	OpenAI: text-davinci-003, code-davinci-002, GPT-3.5-turbo, GPT-4-turbo, GPT-4-32k
-	Salesforce: CodeGen-6B, CodeGen2.5-7B
Results may vary if TiCoder is used with a different model, based on its unique design, configuration and training. 
The generated code in TiCoder can be:
  1. Incorrect: does not reliably perform the intended action  
  2. Insecure: does not adhere to security best-practices and is vulnerable to attacks or misuse  
  3. Malware-containing: designed to exploit the system it resides in or interacts with 
However, all code harms are inherited directly from the base code generation model as TiCoder only provides a re-ranking of the generate code snippets. To evaluate these code harms, the Azure AI Foundry evaluator for code harms, including malicious and vulnerable code generation can be used. 

## EVALUATION RESULTS
At a high level, we found that TiCoder provided an average absolute improvement of 45.97% in the pass@1 code generation accuracy for both datasets and across all LLMs within 5 user interactions. We evaluate gpt-35-turbo for harms related to code generation using Azure AI Foundry. We use 20 prompt attempting to generate malicious code, 6/20 prompts resulted in generated code that is labeled as vulnerable.

## LIMITATIONS
TiCoder was developed for research and experimental purposes. Further testing and validation are needed before considering its application in commercial or real-world scenarios.
TiCoder may not scale to more complex code generation tasks. For example, in cases where the user is unable to validate tests, e.g. for tests that require intricate testing frameworks, the workflow may not be tenable. 
The utility of the interactive framework is contingent upon (a) the ability of LLMs to generate useful tests, and (b) the cost-benefit trade-off of the overhead of user interaction versus the benefit on pruning and ranking of code suggestions.
TiCoder was designed and tested using the English language. Performance in other languages may vary and should be assessed by someone who is both an expert in the expected outputs and a native speaker of that language.
Outputs generated by AI may include factual errors, fabrication, or speculation. Users are responsible for assessing the accuracy of generated content. All decisions leveraging outputs of the system should be made with human oversight and not be based solely on system outputs.
TiCoder inherits any biases, errors, or omissions produced by its base model. Developers are advised to choose an appropriate base LLM/MLLM carefully, depending on the intended use case. 
There has not been a systematic effort to ensure that systems using TiCoder are protected from security vulnerabilities such as indirect prompt injection attacks. Any systems using it should take proactive measures to harden their systems as appropriate.

## BEST PRACTICES
We strongly encourage users to use LLMs that support robust Responsible AI mitigations, such as Azure Open AI (AOAI) services. Such services continually update their safety and RAI mitigations with the latest industry standards for responsible use. For more on AOAI’s best practices when employing foundations models for scripts and applications:
  -	[Blog post on responsible AI features in AOAI that were presented at Ignite 2023](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/announcing-new-ai-safety-amp-responsible-ai-features-in-azure/ba-p/3983686)
  -	[Overview of Responsible AI practices for Azure OpenAI models] (https://learn.microsoft.com/en-us/legal/cognitive-services/openai/overview)
  -	[Azure OpenAI Transparency Note](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/transparency-note)
  -	[OpenAI’s Usage policies](https://openai.com/policies/usage-policies)
  -	[Azure OpenAI’s Code of Conduct](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/code-of-conduct)

## CONTACT
We welcome feedback and collaboration from our audience. If you have suggestions, questions, or observe unexpected/offensive behavior in our technology, please contact us at sfakhoury@microsoft.com
If the team receives reports of undesired behavior or identifies issues independently, we will update this repository with appropriate mitigations.

