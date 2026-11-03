"""Business and Compliance Operational Metrics."""

from typing import Dict, Any


class BusinessMetricsCalculator:
    """Calculates high-level business impact, operational ROI, and compliance conversion."""

    @staticmethod
    def calculate_conversion_rate(validated_sars: int, total_alerts: int) -> float:
        """
        Alert-to-SAR Conversion Rate:
        Conversion Rate = Validated SAR Filings / Total Alerts Triggered
        Target: > 25% (Legacy baseline: 1-2%)
        """
        if total_alerts <= 0:
            return 0.0
        return round(validated_sars / total_alerts, 4)

    @staticmethod
    def calculate_mtti_reduction(baseline_hours: float, current_minutes: float) -> Dict[str, float]:
        """
        Mean Time to Investigate (MTTI) reduction:
        Baseline: 4.0 hours (240 mins) -> Target: < 20.0 minutes
        """
        baseline_mins = baseline_hours * 60.0
        reduction_mins = max(0.0, baseline_mins - current_minutes)
        reduction_pct = (reduction_mins / max(baseline_mins, 1.0)) * 100.0

        return {
            "current_mtti_minutes": round(current_minutes, 2),
            "baseline_mtti_minutes": round(baseline_mins, 2),
            "time_saved_minutes": round(reduction_mins, 2),
            "efficiency_gain_pct": round(reduction_pct, 2),
        }

    @staticmethod
    def calculate_labor_savings(
        resolved_alerts: int,
        hourly_analyst_rate: float = 65.0,
        baseline_hours_per_alert: float = 4.0,
        ai_minutes_per_alert: float = 15.0,
    ) -> Dict[str, float]:
        """Calculate operational labor dollar savings from autonomous agent triage."""
        legacy_cost = resolved_alerts * baseline_hours_per_alert * hourly_analyst_rate
        ai_labor_cost = resolved_alerts * (ai_minutes_per_alert / 60.0) * hourly_analyst_rate
        net_savings = legacy_cost - ai_labor_cost

        return {
            "resolved_alerts": resolved_alerts,
            "legacy_labor_cost_usd": round(legacy_cost, 2),
            "ai_assisted_labor_cost_usd": round(ai_labor_cost, 2),
            "net_labor_savings_usd": round(net_savings, 2),
        }

    @classmethod
    def compute_all(
        cls,
        total_alerts: int,
        validated_sars: int,
        fiu_rejections: int,
        avg_mtti_minutes: float,
        cost_per_alert: float,
    ) -> Dict[str, Any]:
        """Compute consolidated business impact scorecard."""
        conv_rate = cls.calculate_conversion_rate(validated_sars, total_alerts)
        mtti = cls.calculate_mtti_reduction(baseline_hours=4.0, current_minutes=avg_mtti_minutes)
        labor = cls.calculate_labor_savings(resolved_alerts=total_alerts)
        fiu_rate = round(fiu_rejections / max(validated_sars, 1), 4)

        return {
            "alert_to_sar_conversion_rate": conv_rate,
            "target_conversion_achieved": conv_rate >= 0.25,
            "mtti_metrics": mtti,
            "cost_per_resolved_alert_usd": round(cost_per_alert, 2),
            "fiu_rejection_rate": fiu_rate,
            "labor_savings": labor,
        }
