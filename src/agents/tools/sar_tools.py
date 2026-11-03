"""Suspicious Activity Report (SAR) regulatory taxonomy and mapping tools."""

from typing import List, Dict, Any
from src.core.models import TypologyType


class SARTaxonomyTools:
    """Maps typologies and indicators to official FinCEN / FIU Suspicious Activity Codes."""

    ACTIVITY_CODE_MAP = {
        TypologyType.SMURFING_STRUCTURING: [
            "31_A_STRUCTURING_TRANSACTIONS",
            "31_B_MULTIPLE_BRANCH_DEPOSITS",
            "31_Z_BELOW_CTR_THRESHOLD",
        ],
        TypologyType.RAPID_VELOCITY_PEELING_CHAIN: [
            "32_A_RAPID_MOVEMENT_OF_FUNDS",
            "32_D_PEELING_CHAIN_LAYERING",
            "38_Z_UNUSUAL_USE_OF_MULTIPLE_ACCOUNTS",
        ],
        TypologyType.SLEEPER_MULE_ACTIVATION: [
            "38_B_MONEY_MULE_ACTIVITY",
            "38_C_DORMANT_ACCOUNT_SUDDEN_VOLUME",
            "35_Z_SUSPICIOUS_IDENTITY_INCONSISTENCY",
        ],
        TypologyType.SYNTHETIC_IDENTITY_RING: [
            "35_A_SYNTHETIC_IDENTITY_FRAUD",
            "35_D_SHARED_DEVICE_INFRASTRUCTURE",
            "38_E_CIRCULAR_CREDIT_BUILDING_RING",
        ],
        TypologyType.FRACTIONAL_UBO_CONCEALMENT: [
            "38_G_SHELL_COMPANY_CONCEALMENT",
            "38_H_SUB_THRESHOLD_UBO_PARTITIONING",
            "35_Z_OFFSHORE_OPAQUE_OWNERSHIP",
        ],
        TypologyType.CRYPTO_TO_FIAT_MIXER_BRIDGE: [
            "39_A_UNREGISTERED_VASP_INTERACTION",
            "39_B_PRIVACY_MIXER_DISPERSAL",
            "39_Z_CRYPTO_TO_FIAT_OCT_CREDIT",
        ],
        TypologyType.TRADE_BASED_MONEY_LAUNDERING: [
            "34_A_TBML_OVER_UNDER_INVOICING",
            "34_B_PHANTOM_COMMERCIAL_SHIPPING",
            "34_Z_CUSTOMS_VALUE_DISCREPANCY",
        ],
        TypologyType.ADVERSARIAL_ML_PERTURBATION: [
            "38_Z_THRESHOLD_EVASION_PROBING",
            "38_M_PAYROLL_MIMICRY_ANOMALY",
        ],
        TypologyType.SANCTIONS_HARD_STOP: [
            "30_A_OFAC_SANCTIONS_MATCH",
            "30_B_EMBARGOED_JURISDICTION",
        ],
    }

    @classmethod
    def get_fincen_codes(cls, typology: TypologyType) -> List[str]:
        """Retrieve mandatory FinCEN Suspicious Activity Codes for given typology."""
        return cls.ACTIVITY_CODE_MAP.get(typology, ["38_Z_OTHER_SUSPICIOUS_ACTIVITY"])


sar_tools = SARTaxonomyTools()
