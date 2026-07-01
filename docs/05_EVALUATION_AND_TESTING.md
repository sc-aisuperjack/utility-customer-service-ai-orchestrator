# Evaluation and Testing

Test layers:
- unit tests
- golden cases
- RAG retrieval tests
- tool selection tests
- safety tests
- human SME review

Run:
pytest -q
python -m evals.run_evals

Day-one line:
I would fail a prompt change before a customer sees it by using golden regression cases in CI.
