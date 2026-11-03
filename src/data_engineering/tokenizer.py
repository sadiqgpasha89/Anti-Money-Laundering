"""OpenStack PII Tokenization and Scrubbing Gateway.

Ensures strict compliance with data sovereignty regulations:
Full customer PII (names, SSNs, account numbers) never leaves OpenStack.
Cryptographic deterministic tokenization replaces PII with ephemeral tokens
prior to cross-cloud transit to Google Cloud Platform (GCP).
"""

import hashlib
import hmac
from typing import Dict, Any, Optional
from src.core.config import settings
from src.core.models import Transaction, PartyProfile


class PIITokenizer:
    """Cryptographic PII Tokenizer & Vault for OpenStack-to-GCP Gateway."""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = (secret_key or settings.SECRET_KEY).encode("utf-8")
        # Secure in-memory token vault located strictly within OpenStack boundary
        self._vault: Dict[str, str] = {}
        self._reverse_vault: Dict[str, str] = {}

    def _generate_token(self, pii_type: str, value: str) -> str:
        """Create a deterministic pseudonymized token preserving referential integrity."""
        if not value:
            return ""
        normalized = value.strip().upper()
        h = hmac.new(self.secret_key, f"{pii_type}:{normalized}".encode("utf-8"), hashlib.sha256).hexdigest()
        token = f"TOK_{pii_type}_{h[:12]}"

        # Record in on-premises vault for reversible authorized retrieval
        self._vault[token] = normalized
        self._reverse_vault[f"{pii_type}:{normalized}"] = token
        return token

    def tokenize_party(self, party: PartyProfile) -> PartyProfile:
        """Tokenize a customer or legal entity party profile."""
        tokenized_cust_id = self._generate_token("CUST", party.customer_id)
        tokenized_acct_id = self._generate_token("ACCT", party.account_id)
        tokenized_name = self._generate_token("NAME", party.name)
        tokenized_ssn = self._generate_token("SSN", party.ssn) if party.ssn else None

        return PartyProfile(
            customer_id=tokenized_cust_id,
            account_id=tokenized_acct_id,
            name=tokenized_name,
            ssn=tokenized_ssn,
            country=party.country,
            city=party.city,
            account_tenure_months=party.account_tenure_months,
            historical_monthly_avg_vol=party.historical_monthly_avg_vol,
            risk_rating=party.risk_rating,
            is_pep=party.is_pep,
            is_sanctioned=party.is_sanctioned,
        )

    def tokenize_transaction(self, txn: Transaction) -> Transaction:
        """Tokenize transaction for safe GCP cloud transit."""
        tokenized_sender = self.tokenize_party(txn.sender)
        tokenized_receiver = self.tokenize_party(txn.receiver)

        # Scrub sensitive metadata
        scrubbed_meta = dict(txn.metadata)
        if "declared_shareholders" in scrubbed_meta:
            # Mask names in metadata
            scrubbed_shareholders = []
            for sh in scrubbed_meta["declared_shareholders"]:
                sh_copy = dict(sh)
                sh_copy["name"] = self._generate_token("SH_NAME", sh.get("name", ""))
                scrubbed_shareholders.append(sh_copy)
            scrubbed_meta["declared_shareholders"] = scrubbed_shareholders

        return Transaction(
            transaction_id=txn.transaction_id,
            timestamp=txn.timestamp,
            amount=txn.amount,
            currency=txn.currency,
            channel=txn.channel,
            payment_rail=txn.payment_rail,
            sender=tokenized_sender,
            receiver=tokenized_receiver,
            telemetry=txn.telemetry,
            metadata=scrubbed_meta,
            is_tokenized=True,
        )

    def detokenize(self, token: str) -> str:
        """Resolve token back to cleartext PII (restricted to on-premises cockpit)."""
        return self._vault.get(token, token)

    def get_token(self, pii_type: str, raw_value: str) -> Optional[str]:
        """Look up existing token for a given raw value."""
        return self._reverse_vault.get(f"{pii_type}:{raw_value.strip().upper()}")

    def clear_vault(self):
        """Clear the vault cache (for testing)."""
        self._vault.clear()
        self._reverse_vault.clear()


# Global singleton tokenizer
pii_tokenizer = PIITokenizer()
