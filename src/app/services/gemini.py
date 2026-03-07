import json
import re
from typing import Any, Iterable

from google import genai
from google.genai import types

from app.models import COMPONENTS


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "greenbuild-project"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


class GeminiService:
    def __init__(self, api_key: str, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if api_key and api_key != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=api_key)

    def _fallback_analysis(self, payload: dict[str, Any], climate: dict[str, Any]) -> dict[str, Any]:
        base_materials = {
            "Foundation": "Conventional reinforced concrete slab",
            "Structure": payload["structure"],
            "Walls": "Standard CMU cavity wall",
            "Roof": "Dark membrane roof assembly",
            "Insulation": "Fiberglass batt insulation",
            "Windows": "Double-glazed aluminum windows",
            "Doors": "Standard hollow metal exterior doors",
            "HVAC": "Conventional packaged rooftop units",
            "Flooring": "Virgin vinyl tile",
            "Interior Finishes": "Standard gypsum and solvent-heavy paint",
        }
        material_sets = {
            "Foundation": ["LC3 concrete", "Geopolymer concrete", "Recycled aggregate concrete"],
            "Structure": ["Mass timber hybrid frame", "High-recycled steel frame", "Low-cement precast system"],
            "Walls": ["Hemp-lime wall system", "AAC block wall", "Recycled steel stud wall"],
            "Roof": ["Cool roof membrane", "CLT roof with bio-based topping", "Recycled metal standing seam roof"],
            "Insulation": ["Cellulose insulation", "Wood fiber insulation", "Mineral wool insulation"],
            "Windows": ["Triple-glazed fiberglass windows", "Low-e timber-aluminum windows", "Vacuum insulated glazing"],
            "Doors": ["FSC timber composite doors", "Recycled steel insulated doors", "Thermally broken aluminum doors"],
            "HVAC": ["Air-source heat pump VRF", "Dedicated outdoor air with ERV", "Ground-source heat pump"],
            "Flooring": ["Bamboo flooring", "Polished low-carbon concrete", "Recycled rubber flooring"],
            "Interior Finishes": ["Low-VOC lime paint", "Recycled gypsum board", "Bio-based acoustic panels"],
        }
        components = []
        temp_factor = climate.get("temperature_c", 24) / 30
        humidity_factor = climate.get("humidity_pct", 50) / 100
        for index, component in enumerate(COMPONENTS):
            alternatives = []
            for rank, material in enumerate(material_sets[component], start=1):
                carbon = round(_clamp(18 + index * 1.4 + rank * 6 + temp_factor * 5, 12, 68), 1)
                cost = round(_clamp(-2 + index * 0.4 + rank * 2.6, -8, 18), 1)
                speed = round(_clamp(6 - index * 0.35 - rank * 1.5 - humidity_factor * 4, -10, 10), 1)
                score = round(_clamp(68 + carbon * 0.35 - cost * 0.4 + speed * 0.55, 55, 96), 1)
                alternatives.append(
                    {
                        "name": material,
                        "summary": f"Ranked option {rank} for {component.lower()} with strong lifecycle gains and climate resilience.",
                        "carbon_reduction_pct": carbon,
                        "cost_delta_pct": cost,
                        "speed_delta_pct": speed,
                        "sustainability_score": score,
                        "rationale": f"Performs well for {payload['location']} conditions while balancing embodied carbon and delivery risk.",
                    }
                )
            components.append(
                {
                    "component": component,
                    "baseline": base_materials[component],
                    "climate_note": f"Adjust detailing for {climate['temperature_c']}C conditions, humidity {climate['humidity_pct']}%, and wind {climate['wind_speed_kph']} kph.",
                    "recommendation_summary": f"Target {component.lower()} upgrades early because they materially shift embodied carbon and operations.",
                    "alternatives": alternatives,
                }
            )

        best_options = [component["alternatives"][0] for component in components]
        return {
            "executive_summary": (
                f"{payload['project_name']} can materially reduce embodied carbon by prioritizing envelope upgrades, "
                f"electrified HVAC, and lower-cement structural systems tuned to {climate['location_label']}."
            ),
            "components": components,
            "implementation_notes": [
                "Validate local code and fire requirements before locking structural substitutions.",
                "Run supplier lead-time checks on the top-ranked option for each component.",
                "Pair envelope improvements with HVAC resizing to capture compound savings.",
            ],
            "summary_metrics": {
                "total_estimated_carbon_reduction_pct": round(sum(item["carbon_reduction_pct"] for item in best_options) / len(best_options), 1),
                "average_cost_delta_pct": round(sum(item["cost_delta_pct"] for item in best_options) / len(best_options), 1),
                "average_delivery_speed_delta_pct": round(sum(item["speed_delta_pct"] for item in best_options) / len(best_options), 1),
                "average_sustainability_score": round(sum(item["sustainability_score"] for item in best_options) / len(best_options), 1),
            },
        }

    def _prompt(self, payload: dict[str, Any], climate: dict[str, Any]) -> str:
        return f"""
You are a sustainable construction advisor. Produce strict JSON only.

Project input:
{json.dumps(payload, indent=2)}

Climate input:
{json.dumps(climate, indent=2)}

Return JSON with this exact top-level shape:
{{
  "executive_summary": "string",
  "summary_metrics": {{
    "total_estimated_carbon_reduction_pct": number,
    "average_cost_delta_pct": number,
    "average_delivery_speed_delta_pct": number,
    "average_sustainability_score": number
  }},
  "implementation_notes": ["string", "string", "string"],
  "components": [
    {{
      "component": "Foundation",
      "baseline": "string",
      "climate_note": "string",
      "recommendation_summary": "string",
      "alternatives": [
        {{
          "name": "string",
          "summary": "string",
          "carbon_reduction_pct": number,
          "cost_delta_pct": number,
          "speed_delta_pct": number,
          "sustainability_score": number,
          "rationale": "string"
        }}
      ]
    }}
  ]
}}

Requirements:
- Include exactly these 10 components: {", ".join(COMPONENTS)}.
- For each component include exactly 3 ranked alternatives sorted best to third best.
- Carbon reduction is percent reduction versus conventional baseline.
- Cost delta is percent change versus baseline.
- Speed delta is percent faster positive, slower negative.
- Sustainability score is 0-100.
- Keep numbers realistic and climate-aware.
- No markdown, no commentary outside JSON.
""".strip()

    def _normalize_analysis(self, raw: dict[str, Any], payload: dict[str, Any], climate: dict[str, Any]) -> dict[str, Any]:
        fallback = self._fallback_analysis(payload, climate)
        components_by_name = {
            component["component"]: component for component in raw.get("components", []) if component.get("component")
        }
        normalized_components = []
        for fallback_component in fallback["components"]:
            component_name = fallback_component["component"]
            candidate = components_by_name.get(component_name, {})
            alternatives = candidate.get("alternatives") or []
            normalized_alts = []
            for index, fallback_alt in enumerate(fallback_component["alternatives"]):
                source = alternatives[index] if index < len(alternatives) and isinstance(alternatives[index], dict) else {}
                normalized_alts.append(
                    {
                        "name": source.get("name") or fallback_alt["name"],
                        "summary": source.get("summary") or fallback_alt["summary"],
                        "carbon_reduction_pct": round(float(source.get("carbon_reduction_pct", fallback_alt["carbon_reduction_pct"])), 1),
                        "cost_delta_pct": round(float(source.get("cost_delta_pct", fallback_alt["cost_delta_pct"])), 1),
                        "speed_delta_pct": round(float(source.get("speed_delta_pct", fallback_alt["speed_delta_pct"])), 1),
                        "sustainability_score": round(_clamp(float(source.get("sustainability_score", fallback_alt["sustainability_score"])), 0, 100), 1),
                        "rationale": source.get("rationale") or fallback_alt["rationale"],
                    }
                )
            normalized_components.append(
                {
                    "component": component_name,
                    "baseline": candidate.get("baseline") or fallback_component["baseline"],
                    "climate_note": candidate.get("climate_note") or fallback_component["climate_note"],
                    "recommendation_summary": candidate.get("recommendation_summary") or fallback_component["recommendation_summary"],
                    "alternatives": normalized_alts,
                }
            )

        summary_metrics = raw.get("summary_metrics") or fallback["summary_metrics"]
        implementation_notes = raw.get("implementation_notes") or fallback["implementation_notes"]
        return {
            "executive_summary": raw.get("executive_summary") or fallback["executive_summary"],
            "summary_metrics": {
                "total_estimated_carbon_reduction_pct": round(float(summary_metrics.get("total_estimated_carbon_reduction_pct", fallback["summary_metrics"]["total_estimated_carbon_reduction_pct"])), 1),
                "average_cost_delta_pct": round(float(summary_metrics.get("average_cost_delta_pct", fallback["summary_metrics"]["average_cost_delta_pct"])), 1),
                "average_delivery_speed_delta_pct": round(float(summary_metrics.get("average_delivery_speed_delta_pct", fallback["summary_metrics"]["average_delivery_speed_delta_pct"])), 1),
                "average_sustainability_score": round(_clamp(float(summary_metrics.get("average_sustainability_score", fallback["summary_metrics"]["average_sustainability_score"])), 0, 100), 1),
            },
            "implementation_notes": implementation_notes[:4],
            "components": normalized_components,
        }

    def generate_analysis(self, payload: dict[str, Any], climate: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return self._fallback_analysis(payload, climate)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=self._prompt(payload, climate),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            text = response.text if hasattr(response, "text") else ""
            data = json.loads(text)
            return self._normalize_analysis(data, payload, climate)
        except Exception:
            return self._fallback_analysis(payload, climate)

    def stream_chat(self, result: dict[str, Any], message: str) -> Iterable[str]:
        if not self.client:
            answer = (
                f"For {result['project_name']}, focus on the top-ranked {result['components'][0]['component'].lower()} "
                f"and HVAC moves first. {message.strip()} maps back to climate resilience, embodied carbon, and supplier timing."
            )
            for chunk in re.findall(r".{1,28}", answer):
                yield chunk
            return

        prompt = f"""
You are GreenBuild AI. Answer the follow-up question using the stored project result.
Be concise, practical, and specific to the recommendations.

Project result:
{json.dumps(result, indent=2)}

User question:
{message}
""".strip()
        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.5),
            )
            for chunk in response:
                text = getattr(chunk, "text", "")
                if text:
                    yield text
        except Exception:
            fallback = "I could not reach Gemini for a live follow-up, so use the highest scoring envelope and HVAC options as the default recommendation set."
            for chunk in re.findall(r".{1,28}", fallback):
                yield chunk
