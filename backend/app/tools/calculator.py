import math
import re
from typing import Dict, Any, List

class MarketCalculator:
    @staticmethod
    def derive_from_sources(query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate a projection only when source text states the required inputs."""
        target_matches = re.findall(r"\b(20\d{2})\b", query)
        if not target_matches:
            return {"status": "insufficient", "reason": "No target year was specified."}
        target_year = int(target_matches[-1])
        sentences = []
        for chunk in chunks:
            sentences.extend(re.split(r"(?<=[.!?])\s+", str(chunk.get("text", ""))))

        base = None
        for sentence in sentences:
            if not re.search(r"valued|valuation|market size|market stood|market reached", sentence, re.IGNORECASE):
                continue
            value_match = re.search(r"(?:USD\s*)?([0-9][0-9,]*(?:\.\d+)?)\s*(?:billion|bn|B)\b", sentence, re.IGNORECASE)
            year_match = re.search(r"\b(20\d{2})\b", sentence)
            if value_match and year_match:
                base = (float(value_match.group(1).replace(",", "")), int(year_match.group(1)), sentence)
                break

        cagr = None
        for sentence in sentences:
            cagr_match = re.search(r"CAGR(?:\s+of)?\s*(?:at\s*)?([0-9]+(?:\.\d+)?)\s*%", sentence, re.IGNORECASE)
            if not cagr_match:
                continue
            period_match = re.search(r"\b(20\d{2})\s*(?:-|–|to|through|and)\s*(20\d{2})\b", sentence, re.IGNORECASE)
            if period_match:
                start_year, end_year = int(period_match.group(1)), int(period_match.group(2))
            else:
                end_match = re.search(r"(?:through|towards|until|by)\s+(20\d{2})", sentence, re.IGNORECASE)
                if not end_match or base is None:
                    continue
                end_year = int(end_match.group(1))
                start_year = base[1] + 1
            cagr = (float(cagr_match.group(1)), start_year, end_year, sentence)
            break

        if not base or not cagr:
            return {"status": "insufficient", "reason": "The subscribed sources do not state a usable base value and CAGR."}
        base_value, base_year, base_sentence = base
        rate, cagr_start, forecast_end, cagr_sentence = cagr
        if not math.isfinite(base_value) or base_value <= 0 or not math.isfinite(rate) or rate < -100 or rate > 1000:
            return {"status": "insufficient", "reason": "The source values are outside the supported calculation range."}
        if target_year > forecast_end:
            return {"status": "beyond_horizon", "forecast_end": forecast_end}
        if target_year <= base_year:
            return {"status": "insufficient", "reason": "The requested year is not after the stated base year."}
        if target_year < cagr_start:
            return {"status": "insufficient", "reason": "The requested year is before the source's stated CAGR period."}

        years = target_year - base_year
        global_value = base_value * ((1 + rate / 100) ** years)
        region = "Global"
        share = 100.0
        share_sentence = None
        if re.search(r"\bAPAC\b|Asia-Pacific", query, re.IGNORECASE):
            region = "APAC"
            share = None
            for sentence in sentences:
                if re.search(r"APAC|Asia-Pacific", sentence, re.IGNORECASE):
                    share_match = re.search(r"([0-9]+(?:\.\d+)?)\s*%", sentence)
                    context = sentence.lower()
                    describes_share = any(term in context for term in ["share", "accounted for", "represented", "portion", "revenue"])
                    if share_match and describes_share and 0 <= float(share_match.group(1)) <= 100:
                        share = float(share_match.group(1))
                        share_sentence = sentence
                        break
            if share is None:
                return {"status": "insufficient", "reason": "No APAC share is stated in the subscribed sources."}
        value = global_value * share / 100
        formula = f"{base_value:.2f} * (1 + {rate / 100:.4f})^{years}"
        if share < 100:
            formula += f" * ({share:.2f} / 100)"
        assumptions = [
            f"Base value USD {base_value:.2f} B is from {base_year}.",
            f"CAGR of {rate:.2f}% is applied as a constant annual rate.",
            f"The calculation compounds for {years} years through {target_year}.",
        ]
        if cagr_start != base_year:
            alternate_years = max(0, target_year - cagr_start)
            alternate = base_value * ((1 + rate / 100) ** alternate_years) * share / 100
            assumptions.append(
                f"Period ambiguity: using the CAGR's stated start year {cagr_start} instead gives USD {alternate:.2f} B."
            )
        if share < 100:
            assumptions.append(f"The {region} share of {share:.2f}% is assumed constant through {target_year}.")
        return {
            "status": "derived",
            "metric": f"{region} market projection {target_year}",
            "value": f"USD {value:.2f} B",
            "formula": formula,
            "assumptions": assumptions,
            "source_sentences": [base_sentence, cagr_sentence] + ([share_sentence] if share_sentence else []),
        }

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
