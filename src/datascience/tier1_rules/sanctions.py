"""Sanctions and PEP String Screening Gateway.

Implements high-performance phonetic, Levenshtein, and Jaro-Winkler string matching
against global sanctions watchlists (OFAC, EU, UN, UK HMT).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.core.config import settings
from src.core.models import RuleHit


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """Compute Jaro-Winkler string similarity metric in [0.0, 1.0]."""
    s1, s2 = s1.upper().strip(), s2.upper().strip()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = (max(len1, len2) // 2) - 1
    if max_dist < 0:
        max_dist = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (
        (matches / len1)
        + (matches / len2)
        + ((matches - transpositions / 2.0) / matches)
    ) / 3.0

    # Winkler prefix bonus (up to 4 characters)
    prefix_len = 0
    for i in range(min(4, min(len1, len2))):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + (prefix_len * 0.1 * (1.0 - jaro))


def soundex(name: str) -> str:
    """Standard American Soundex phonetic encoder."""
    name = "".join(c for c in name.upper() if c.isalpha())
    if not name:
        return "0000"

    soundex_map = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }

    first_letter = name[0]
    tail = name[1:]

    coded = []
    prev_code = soundex_map.get(first_letter, "")
    for char in tail:
        code = soundex_map.get(char, "")
        if code != prev_code:
            if code != "":
                coded.append(code)
            prev_code = code

    res = first_letter + "".join(coded)
    return (res + "0000")[:4]


class SanctionsMatcher:
    """High-speed in-memory sanctions matcher."""

    def __init__(self, sanctions_file: Optional[Path] = None):
        self.file_path = sanctions_file or settings.SANCTIONS_PATH
        self._sanctions_data: List[Dict[str, Any]] = []
        self._load_sanctions()

    def _load_sanctions(self):
        """Load sanctions roster into memory."""
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._sanctions_data = json.load(f)

    def match_name(self, candidate_name: str, threshold: float = 0.85) -> List[Tuple[Dict[str, Any], float]]:
        """Fuzzy match candidate against sanctions list names and aliases."""
        candidate_clean = candidate_name.upper().strip()
        candidate_soundex = soundex(candidate_clean)
        results = []

        for record in self._sanctions_data:
            target_name = record["name"].upper().strip()
            score = jaro_winkler_similarity(candidate_clean, target_name)
            phonetic_bonus = 0.05 if soundex(target_name) == candidate_soundex else 0.0
            adjusted_score = min(1.0, score + phonetic_bonus)

            best_score = adjusted_score

            # Check aliases
            for alias in record.get("aliases", []):
                alias_score = jaro_winkler_similarity(candidate_clean, alias.upper().strip())
                if alias_score > best_score:
                    best_score = alias_score

            if best_score >= threshold:
                results.append((record, best_score))

        # Sort descending by match score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def check_hard_stop(self, candidate_name: str, candidate_country: str) -> Optional[RuleHit]:
        """Evaluate whether party triggers a non-negotiable statutory hard stop."""
        matches = self.match_name(candidate_name, threshold=settings.SANCTIONS_JARO_THRESHOLD)
        if matches:
            record, score = matches[0]
            return RuleHit(
                rule_id="RULE_SANC_001",
                rule_name="SANCTIONS_HARD_STOP",
                is_hard_stop=True,
                confidence=round(score, 3),
                description=f"Direct match against {record['list_source']} ({record['program']}) for entity '{record['name']}'",
                trigger_value={
                    "matched_entity": record["name"],
                    "sanctions_id": record["id"],
                    "list_source": record["list_source"],
                    "score": score,
                },
            )

        # Check sanctioned country
        if candidate_country.upper() in ["KP", "IR", "SY"]:
            return RuleHit(
                rule_id="RULE_SANC_002",
                rule_name="EMBARGOED_JURISDICTION_HARD_STOP",
                is_hard_stop=True,
                confidence=1.0,
                description=f"FATF High-Risk Embargoed Jurisdiction: '{candidate_country.upper()}'",
                trigger_value={"country": candidate_country.upper()},
            )

        return None


sanctions_matcher = SanctionsMatcher()
