"""Unit tests for OpenStack PII Tokenizer & Scrubbing Gateway."""

import pytest
from src.data_engineering.tokenizer import PIITokenizer


def test_pii_tokenizer_deterministic_and_reversible(sample_transaction):
    """Test deterministic tokenization and reversible on-premises vault."""
    tokenizer = PIITokenizer(secret_key="test-key-2026")

    # 1. Determinism
    t1 = tokenizer._generate_token("NAME", "JOHN DOE")
    t2 = tokenizer._generate_token("NAME", "JOHN DOE")
    assert t1 == t2
    assert t1.startswith("TOK_NAME_")

    # 2. Transaction Tokenization
    tokenized = tokenizer.tokenize_transaction(sample_transaction)
    assert tokenized.is_tokenized is True
    assert tokenized.sender.name.startswith("TOK_NAME_")
    assert tokenized.sender.customer_id.startswith("TOK_CUST_")
    assert tokenized.sender.ssn.startswith("TOK_SSN_")

    # 3. Vault Detokenization
    recovered_name = tokenizer.detokenize(tokenized.sender.name)
    assert recovered_name == "JANE DOE"
