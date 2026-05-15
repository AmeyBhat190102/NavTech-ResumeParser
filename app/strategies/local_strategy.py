"""
Local model strategy using HuggingFace Transformers.

Architecture:
  1. NER pass  — dslim/bert-base-NER  → extracts named entities (PER, ORG, LOC)
  2. Gen pass  — a small instruction-tuned LLM → produces full structured JSON

The NER entities are injected into the generative prompt as hints, improving
accuracy without requiring a large model for the generative step.

⚠️  GPU recommended for the generative model. Set LOCAL_DEVICE=cpu in .env
    to run on CPU (slow but functional for small models / testing).
"""
from __future__ import annotations

import json
import re
import logging
from functools import cached_property
from typing import Any

from app.core.config import settings
from app.models.resume import ParsedResume
from app.strategies.base import BaseExtractionStrategy, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LocalModelStrategy(BaseExtractionStrategy):
    """HuggingFace-based extraction: NER for hints + generative model for JSON."""

    # ── Lazy-loaded pipelines (avoid import cost at startup) ──────────────────

    @cached_property
    def _ner_pipeline(self):
        from transformers import pipeline  # type: ignore
        logger.info("Loading NER model: %s", settings.local_ner_model)
        return pipeline(
            "ner",
            model=settings.local_ner_model,
            aggregation_strategy="simple",
            device=0 if settings.local_device == "cuda" else -1,
        )

    @cached_property
    def _gen_pipeline(self):
        from transformers import pipeline  # type: ignore
        logger.info("Loading generative model: %s", settings.local_gen_model)
        return pipeline(
            "text-generation",
            model=settings.local_gen_model,
            device_map="auto" if settings.local_device != "cpu" else None,
            torch_dtype="auto",
        )

    @property
    def strategy_name(self) -> str:
        return f"local/{settings.local_gen_model}"

    # ── Main entry point ──────────────────────────────────────────────────────

    async def extract(self, resume_text: str) -> ParsedResume:
        # Step 1: cheap NER pass for entity hints
        ner_hints = self._run_ner(resume_text[:2000])  # NER on first 2000 chars

        # Step 2: generative pass for full structured output
        prompt = self._build_prompt(resume_text, ner_hints)
        raw_json = self._run_generation(prompt)

        data = self._safe_parse_json(raw_json)
        parsed = ParsedResume(**data)
        parsed.strategy_used = self.strategy_name
        return parsed

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _run_ner(self, text: str) -> dict[str, list[str]]:
        """Return grouped named entities as hints for the generative prompt."""
        try:
            entities = self._ner_pipeline(text)
        except Exception as exc:
            logger.warning("NER pass failed: %s", exc)
            return {}

        grouped: dict[str, list[str]] = {}
        for ent in entities:
            label = ent.get("entity_group", "")
            word = ent.get("word", "").strip()
            if label and word:
                grouped.setdefault(label, [])
                if word not in grouped[label]:
                    grouped[label].append(word)
        return grouped

    def _build_prompt(self, resume_text: str, ner_hints: dict[str, list[str]]) -> str:
        hint_lines = ""
        if ner_hints:
            hint_lines = "\n\nNER hints (use as guidance, not gospel):\n"
            for label, words in ner_hints.items():
                hint_lines += f"  {label}: {', '.join(words)}\n"

        return (
            f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n"
            f"Parse the following resume:{hint_lines}\n\n"
            f"{resume_text}\n[/INST]"
        )

    def _run_generation(self, prompt: str) -> str:
        result = self._gen_pipeline(
            prompt,
            max_new_tokens=2048,
            do_sample=False,
            temperature=1.0,     # ignored when do_sample=False; avoids deprecation warning
            pad_token_id=2,
        )
        generated: str = result[0]["generated_text"]
        # Strip the prompt prefix — pipeline returns prompt + completion
        if "[/INST]" in generated:
            generated = generated.split("[/INST]", 1)[-1]
        return generated.strip()

    def _safe_parse_json(self, text: str) -> dict[str, Any]:
        """Best-effort JSON extraction from model output."""
        # Strip markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: find the outermost { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.error("Failed to parse JSON from local model output: %s", text[:500])
        return {}
