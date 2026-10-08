---
language:
  - en
license: apache-2.0
size_categories:
  - n<1K
task_categories:
  - question-answering
pretty_name: StayLocal
dataset_info:
  config_name: default
  features:
    - name: instance_id
      dtype: string
    - name: subset
      dtype: string
    - name: level
      dtype: string
    - name: phenomenon
      dtype: string
    - name: document
      dtype: string
    - name: gold
      dtype: string
    - name: evidence
      dtype: string
    - name: abstain
      dtype: string
  splits:
    - name: test
      num_examples: 140
configs:
  - config_name: default
    data_files:
      - split: test
        path: data/test.jsonl
---

# StayLocal

Open-book extraction. A row is a document, a gold field map, the evidence spans that must appear in the document, and the fields that must stay empty.

The primary metric is instance accuracy. An instance is correct only if every gold field matches, every evidence span is the span stored on the row and occurs in the document, and every abstain field is empty. Field accuracy, evidence accuracy, abstention accuracy, and false-answer rate are reported beside it. Scores are also broken out by `subset` and `level`.

This split was written by the author of the gold. It is a schema and a scorer, not a filing-derived set. A ceiling replay of the gold scores 1.0. That is a metric check, not a system result.

## Splits

`test`: 140 rows. Seven subsets (meetings, finance, legal, people, sales, ops, knowledge) by four levels (L1 single span, L2 distractor, L3 multi-record or gap, L4 must abstain), five rows each.

## Scoring

`evaluate.py` reads `data/test.jsonl` and a prediction file keyed by `instance_id`. Each prediction has `fields` and `evidence`. No model call is inside the scorer.

## Leaderboard

`eval.yaml` is the Hub benchmark registration file. The dataset does not appear as an official Hub benchmark until Hugging Face allow-lists it. A model score belongs in the model repo at `.eval_results/staylocal.yaml`, pointing at this dataset revision, not in this repo.
