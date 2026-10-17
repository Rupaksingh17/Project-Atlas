import math
from typing import Dict, Any, List

class MarketCalculator:
    @staticmethod
    def calculate_cagr_projection(
        base_value: float,
        cagr_percent: float,
        start_year: int,
        target_year: int,
        share_percent: float = 100.0
    ) -> Dict[str, Any]:
        years = target_year - start_year
        if years < 0:
            raise ValueError("Target year must be greater than or equal to start year.")
            
        rate = cagr_percent / 100.0
        projected_global = base_value * ((1.0 + rate) ** years)
        projected_regional = projected_global * (share_percent / 100.0)
        
        formula = f"{base_value:.2f} * (1 + {rate:.3f})^{years}"
        if share_percent < 100.0:
            formula += f" * ({share_percent:.1f} / 100)"
            
        assumptions = [
            f"Base year {start_year} value taken as USD {base_value:.2f} B",
            f"Compound Annual Growth Rate assumed constant at {cagr_percent:.1f}%",
            f"Forecast duration spans {years} compounding intervals ({start_year} to {target_year})",
            "Note ambiguity: If compounding commences from 2025 rather than 2024, the result reduces by one growth interval"
        ]
        if share_percent < 100.0:
            assumptions.append(f"Regional share assumed stable at {share_percent:.1f}% through {target_year}")
            
        return {
            "value": f"USD {projected_regional:.2f} B",
            "numeric_value": round(projected_regional, 2),
            "formula": formula,
            "assumptions": assumptions,
            "nature": "derived_estimate"
        }

    @staticmethod
    def check_forecast_horizon(target_year: int, max_forecast_year: int = 2030) -> bool:
        return target_year <= max_forecast_year

calculator = MarketCalculator()
