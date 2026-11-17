# Hints · The answer is in the docs

## Look at what was retrieved
Pick one complaint and print `retrieve(question, index)`. Is the handbook sentence that answers it in there, whole? If not, the model never had a chance, and no prompt wording will fix it.

## Chunks cut sentences in half
`build_index` cuts every 220 characters, wherever that lands. A fact that straddles a cut exists in no chunk, and most chunks have lost the heading that says what they are about. Split on sections and sentences instead, and keep the heading with each chunk.

## "vpn" is not "VPN", and "laptops?" is not "laptops"
`score` compares raw words. Case, punctuation and plurals all break a match, while "the" and "do" count as much as "parental". Lowercase both sides, strip punctuation, drop the filler words and reduce words to a stem. Then let rare words count for more than common ones.

## The model answers anyway
When the excerpts do not hold the answer, the prompt gives the model no way out, so it produces something plausible. Tell it to answer only from the excerpts and to say it does not know otherwise. `harness/llm.py` describes exactly how the model reacts.

## Why did the eval say 100%?
Read `data/eval_questions.jsonl` next to the handbook. Every question reuses the handbook's own words, in the handbook's own order. Nobody types like that. Build your tests from the questions people actually asked, starting with `data/user_reports.jsonl`.
