"""Custom domain exceptions for AML Hybrid Architecture."""


class AMLException(Exception):
    """Base AML exception."""
    pass


class SanctionsHardStopException(AMLException):
    """Raised when an incoming transaction matches a statutory hard sanctions list."""
    def __init__(self, message: str, entity_name: str, program: str):
        super().__init__(message)
        self.entity_name = entity_name
        self.program = program


class TokenizationException(AMLException):
    """Raised on PII tokenization/detokenization failures."""
    pass


class CriticRejectionException(AMLException):
    """Raised when the Compliance Critic flags ungrounded assertions in a SAR narrative."""
    def __init__(self, message: str, groundedness_score: float, ungrounded_claims: list):
        super().__init__(message)
        self.groundedness_score = groundedness_score
        self.ungrounded_claims = ungrounded_claims


class SafeDegradationActiveException(AMLException):
    """Raised when cloud interconnect drops and system enters safe degradation mode."""
    pass
