import json

import httpx

from stromwart.contracts.agents import AnalystFinding, ToolResult
from stromwart.errors import ProviderUnavailableError


class AnthropicProvider:
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
            f"{self._base_url}/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self._model,
                "max_tokens": 1200,
                "temperature": 0,
                "system": (
                    "Return JSON only. Produce a grounded incident finding "
                    "using only supplied evidence IDs."
                ),
                "messages": [
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
                    }
                ],
            },
        )

        if response.is_error:
            raise ProviderUnavailableError(
                f"anthropic provider returned {response.status_code}"
            )

        try:
            content = response.json()["content"][0]["text"]
            return AnalystFinding.model_validate_json(content)
        except (KeyError, IndexError, ValueError) as error:
            raise ProviderUnavailableError(
                "anthropic provider returned invalid analyst output"
            ) from error
