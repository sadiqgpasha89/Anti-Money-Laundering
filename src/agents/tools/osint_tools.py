"""OSINT, Adverse Media, and Trade-Based Money Laundering (TBML) Tools."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from src.core.config import settings
from src.data_engineering.tokenizer import pii_tokenizer


class OSINTTools:
    """Agent toolset for adverse media retrieval and commodity price benchmarking."""

    def __init__(
        self,
        media_file: Optional[Path] = None,
        benchmarks_file: Optional[Path] = None,
    ):
        self.media_path = media_file or settings.ADVERSE_MEDIA_PATH
        self.benchmarks_path = benchmarks_file or settings.COMMODITY_BENCHMARKS_PATH
        self._articles: List[Dict[str, Any]] = []
        self._benchmarks: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        if self.media_path.exists():
            with open(self.media_path, "r", encoding="utf-8") as f:
                self._articles = json.load(f)

        if self.benchmarks_path.exists():
            with open(self.benchmarks_path, "r", encoding="utf-8") as f:
                self._benchmarks = json.load(f)

    def search_adverse_media(self, entity_name: str, query_vector: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        Query adverse media via exact/fuzzy entity keyword matching and dense vector similarity.
        Simulates Vertex AI Vector Search.
        """
        results = []
        # Alerts carry tokenized names; resolve the token before matching against media records
        name_clean = pii_tokenizer.detokenize(entity_name).upper().strip()

        for art in self._articles:
            # Check direct entity mention
            mentions = [m.upper().strip() for m in art.get("entities_mentioned", [])]
            name_match = any(name_clean in m or m in name_clean for m in mentions)

            # Check vector cosine similarity if vector provided
            vec_sim = 0.0
            if query_vector and "embedding" in art:
                v1 = np.array(query_vector, dtype=float)
                v2 = np.array(art["embedding"], dtype=float)
                norm = np.linalg.norm(v1) * np.linalg.norm(v2)
                if norm > 0:
                    vec_sim = float(np.dot(v1, v2) / norm)

            relevance = 0.95 if name_match else max(0.0, vec_sim)

            if relevance >= 0.65 or name_match:
                results.append({
                    "article_id": art["article_id"],
                    "title": art["title"],
                    "source": art["source"],
                    "summary": art["summary"],
                    "crime_categories": art["crime_categories"],
                    "severity_score": art["severity_score"],
                    "relevance_score": round(relevance, 3),
                    "url": art["url"],
                })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def verify_tbml_pricing(
        self,
        hs_code: str,
        invoiced_unit_price: float,
    ) -> Dict[str, Any]:
        """
        Verify declared unit prices against international commodity benchmarks:
        Delta_price = |P_invoiced - P_benchmark| / P_benchmark > alpha_tolerance
        """
        commodities = self._benchmarks.get("commodities", {})
        tolerance = self._benchmarks.get("tolerance_percentage", 0.25)

        target = commodities.get(hs_code)
        if not target:
            return {
                "hs_code": hs_code,
                "benchmark_found": False,
                "is_tbml_flagged": False,
                "message": "Commodity code not tracked in standard benchmark catalog.",
            }

        benchmark_price = target["benchmark_price_usd"]
        price_delta = abs(invoiced_unit_price - benchmark_price) / benchmark_price
        is_flagged = price_delta > tolerance

        anomaly_direction = "OVER_INVOICED" if invoiced_unit_price > benchmark_price else "UNDER_INVOICED"

        return {
            "hs_code": hs_code,
            "description": target["description"],
            "benchmark_found": True,
            "benchmark_unit_price_usd": benchmark_price,
            "invoiced_unit_price_usd": invoiced_unit_price,
            "price_delta_ratio": round(price_delta, 3),
            "allowed_tolerance": tolerance,
            "is_tbml_flagged": is_flagged,
            "anomaly_direction": anomaly_direction if is_flagged else "NORMAL",
        }


osint_tools = OSINTTools()
