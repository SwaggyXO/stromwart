import json

import httpx

from stromwart.contracts.agents import AnalystFinding, ToolResult
from stromwart.errors import ProviderUnavailableError


class OpenAiCompatibleProvider:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    async def analyze(
        self,
        incident_context: dict[str, object],
        evidence: list[ToolResult],
    ) -> AnalystFinding:
        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return JSON only. Produce a grounded incident finding "
                            "using only supplied evidence IDs."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "incident": incident_context,
                                "evidence": [
                                    item.model_dump(mode="json") for item in evidence
                                ],
                            }
                        ),
                    },
                ],
            },
        )

        if response.is_error:
            raise ProviderUnavailableError(
                f"openai-compatible provider returned {response.status_code}"
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
            return AnalystFinding.model_validate_json(content)
        except (KeyError, IndexError, ValueError) as error:
            raise ProviderUnavailableError(
                "openai-compatible provider returned invalid analyst output"
            ) from error
