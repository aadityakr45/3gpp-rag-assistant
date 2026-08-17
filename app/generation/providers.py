"""Optional Gemini provider adapter with no import-time network/API effects."""

from __future__ import annotations


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        try:
            from google import genai  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install google-genai for Gemini generation") from exc
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("LLM provider returned an empty response")
        return text
