### Randomize Prompts: Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity

Research-based prompts for mitigating LLM mode collapse (from arXiv:2510.01171):

**1\. Standard burst** \- 10 responses with probability estimates:

| Generate 10 responses to "Tell me a short, original joke about robots." Each response should be approximately 25 words.Return the responses in JSON format with the key "responses" (list of dicts). Each dictionary must include:\- text: the response string only (no explanation or extra text).\- probability: the estimated probability from 0.0 to 1.0 of this response given the input prompt (relative to the full distribution).Give ONLY the JSON object, with no explanations or extra text. |
| :---- |

**2\. Low-probability burst** \- Sample responses below 0.3 probability:

| Generate 10 responses to "Tell me a short, original joke about robots." Each response should be approximately 25 words.Return the responses in JSON format with the key "responses" (list of dicts). Each dictionary must include:\- text: the response string only (no explanation or extra text).\- probability: the estimated probability from 0.0 to 1.0 of this response given the input prompt (relative to the full distribution).Randomly sample the responses from the distribution, with the probability of each response must be below 0.3.Give ONLY the JSON object, with no explanations or extra text. |
| :---- |

**3\. Chain-of-thought burst** \- Reasoning first, then output:

| Generate 5 responses to "Tell me a short, original joke about robots" using chain-of-thought reasoning. Each response should have 30 target words.First, provide a single "reasoning" field as a string, detailing your step-by-step thought process. Then, return the output in JSON format with the key "responses" (list of dicts). Each dictionary must include:\- text: the response string (no explanation or extra text).\- probability: the estimated probability from 0.0 to 1.0 of this response given the input prompt (relative to the full distribution).Give ONLY the JSON object, with no explanations or extra text. |
| :---- |

**4\. Multi-turn burst** \- Spread responses across turns:

| You will generate a total of 12 responses to "Tell me a short, original joke about robots." Each response should be approximately 20 words.First, sample 4 responses.Return the responses in JSON format with the key: "responses" (list of dicts). Each dictionary must include:\- text: the response string (no explanation or extra text).\- confidence: the normalized likelihood score between 0.0 and 1.0 that indicates how representative or typical this response is compared to the full distribution.Give ONLY the JSON object, no explanations or extra text. |
| :---- |
