from typing import Any

import httpx


class ClimateService:
    def __init__(self) -> None:
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_climate(self, location: str) -> dict[str, Any]:
        try:
            # Detect country hint (e.g., "Kochi, India")
            country_hint = None
            search_query = location
            if "," in location:
                parts = [p.strip() for p in location.split(",")]
                search_query = parts[0]
                country_hint = parts[-1].lower()

            with httpx.Client(timeout=20.0) as client:
                geo_response = client.get(
                    self.geocode_url,
                    params={"name": search_query, "count": 10, "language": "en", "format": "json"},
                )
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                results = geo_data.get("results") or []
                if not results:
                    raise ValueError(f"Location not found: {location}")

                # Prioritize based on country hint
                place = results[0]
                if country_hint:
                    for r in results:
                        if country_hint in r.get("country", "").lower():
                            place = r
                            break
                
                latitude = place["latitude"]
                longitude = place["longitude"]
                forecast_response = client.get(
                    self.forecast_url,
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max",
                        "forecast_days": 3,
                        "timezone": "auto",
                    },
                )
                forecast_response.raise_for_status()
                forecast = forecast_response.json()
                current = forecast.get("current", {})
                daily = forecast.get("daily", {})
                next_days_summary = []
                times = daily.get("time", [])
                maxes = daily.get("temperature_2m_max", [])
                mins = daily.get("temperature_2m_min", [])
                rain = daily.get("precipitation_sum", [])
                uv = daily.get("uv_index_max", [])
                for index, day in enumerate(times):
                    next_days_summary.append(
                        f"{day}: {mins[index]}-{maxes[index]}C, rain {rain[index]}mm, UV {uv[index]}"
                    )

                return {
                    "location_label": f"{place['name']}, {place.get('country', '')}".strip(", "),
                    "latitude": latitude,
                    "longitude": longitude,
                    "temperature_c": current.get("temperature_2m", 24),
                    "temp_max": daily.get("temperature_2m_max", [28])[0],
                    "temp_min": daily.get("temperature_2m_min", [18])[0],
                    "wind_speed_kph": current.get("wind_speed_10m", 10),
                    "precipitation_mm": current.get("precipitation", 0),
                    "humidity_pct": current.get("relative_humidity_2m", 50),
                    "next_days_summary": next_days_summary,
                    "source": "Open-Meteo Global Forecasting",
                    "basis": "Daily Extremes (Design Basis)",
                }
        except Exception:
            return {
                "location_label": location,
                "latitude": 0,
                "longitude": 0,
                "temperature_c": 24,
                "wind_speed_kph": 12,
                "precipitation_mm": 1,
                "humidity_pct": 56,
                "next_days_summary": [
                    "Fallback climate profile generated locally.",
                    "Assume moderate heat loading and seasonal precipitation.",
                    "Prioritize resilient envelopes and low-carbon MEP choices.",
                ],
            }

