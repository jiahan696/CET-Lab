"""Provider-agnostic AI Agent gateway.

This is the only network client in the app. It speaks the OpenAI-compatible
`/chat/completions` protocol, which covers DeepSeek, OpenAI, Qwen/DashScope,
Moonshot, local Ollama, and most gateways.  It also supports image input for
vision-capable models (used for scanned answer PDFs).

Configure `ai_config.json` in the same folder as user_data.json.  Nothing is
sent anywhere unless a feature explicitly calls one of the methods below.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .store import default_data_dir


@dataclass(slots=True)
class AIAgentConfig:
    enabled: bool = False
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-flash"
    timeout: int = 120
    temperature: float = 0.2

    @property
    def endpoint(self) -> str:
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.api_key and self.base_url and self.model)


class AIAgentError(RuntimeError):
    pass


def extract_json_object(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model response."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    raise AIAgentError("AI 返回内容不是合法 JSON")


class AIAgentClient:
    """Thin async wrapper with no UI dependency, safe to reuse on mobile."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        self.config_path = (
            Path(config_path)
            if config_path
            else default_data_dir() / "ai_config.json"
        )

    def load_config(self) -> AIAgentConfig:
        if not self.config_path.exists():
            return AIAgentConfig()
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AIAgentConfig()
        cfg = AIAgentConfig()
        for key in ("enabled", "base_url", "api_key", "model", "timeout", "temperature"):
            if key in raw:
                setattr(cfg, key, raw[key])
        cfg.api_key = str(cfg.api_key or os.getenv("CET_AI_API_KEY", ""))
        cfg.base_url = str(
            cfg.base_url or os.getenv("CET_AI_BASE_URL", "https://api.deepseek.com/v1")
        )
        cfg.model = str(cfg.model or os.getenv("CET_AI_MODEL", "deepseek-flash"))
        return cfg

    def save_config(self, cfg: AIAgentConfig) -> Path:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.config_path

    def write_example_config(self) -> Path:
        if not self.config_path.exists():
            self.save_config(AIAgentConfig())
        return self.config_path

    @property
    def available(self) -> bool:
        return self.load_config().configured

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = None,
        max_tokens: int = 4000,
    ) -> str:
        cfg = self.load_config()
        if not cfg.configured:
            raise AIAgentError(
                "AI 接口尚未配置。请打开「AI 设置」填写 API Key 并启用。"
            )
        payload = {
            "model": cfg.model,
            "messages": messages,
            "temperature": cfg.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        return await asyncio.to_thread(self._post, cfg, payload)

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = 0.1,
        max_tokens: int = 6000,
    ) -> dict[str, Any]:
        text = await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return extract_json_object(text)

    def _post(self, cfg: AIAgentConfig, payload: dict[str, Any]) -> str:
        request = urllib.request.Request(
            cfg.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            raise AIAgentError(f"AI 服务返回 HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AIAgentError(f"无法连接 AI 服务: {exc}") from exc
        try:
            data = json.loads(body)
            message = data["choices"][0]["message"]
            content = str(message.get("content") or "").strip()
            if not content:
                raise AIAgentError("AI 返回了空内容，请重试或换一个模型。")
            return content
        except AIAgentError:
            raise
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIAgentError("AI 服务返回了无法解析的内容") from exc

    async def translate_selection(
        self,
        text: str,
        *,
        context: str = "",
        target_language: str = "中文",
    ) -> dict[str, Any]:
        prompt = (
            f"请翻译下面的英文选段为{target_language}。如果选段是一个单词或短语，"
            "请给出词性、音标（若有）和简明释义；如果是句子，请给出自然、准确的中文翻译。\n"
            "返回严格 JSON：{\"translation\":\"...\",\"term\":\"...\","
            "\"phonetic\":\"...\",\"part_of_speech\":\"...\",\"example\":\"...\"}。\n"
            f"上下文（可能为空）：{context[:1200]}\n"
            f"选段：{text}"
        )
        data = await self.chat_json(
            [
                {"role": "system", "content": "你是专业的英汉词典与翻译引擎，只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
        )
        return data

    async def score_writing(
        self,
        *,
        prompt: str,
        answer: str,
        level: str = "CET-4",
        word_limit: tuple[int, int] = (120, 180),
    ) -> dict[str, Any]:
        if not answer.strip():
            return self._empty_subjective("writing")
        system = (
            "你是大学英语四六级写作阅卷老师。按 CET 写作 15 分制评分，"
            "评分维度：内容切题与完整性、组织结构、语言准确性与丰富度、字数。"
            "只输出合法 JSON。"
        )
        user = (
            f"考试级别：{level}\n题目：{prompt}\n字数要求：{word_limit[0]}-{word_limit[1]}\n"
            f"学生作文：\n{answer}\n\n"
            "返回 JSON：{\"score_15\": 0-15 的数字, \"feedback\": \"中文总评 80-150 字\","
            "\"strengths\": [\"...\"], \"improvements\": [\"...\"],"
            "\"corrected_excerpt\": \"挑 1-2 句给出修改示例\"}。"
        )
        data = await self.chat_json(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=6000,
        )
        return self._normalize_subjective(data, "writing")

    async def score_translation(
        self,
        *,
        prompt: str,
        answer: str,
        reference: str = "",
        level: str = "CET-4",
    ) -> dict[str, Any]:
        if not answer.strip():
            return self._empty_subjective("translation")
        system = (
            "你是大学英语四六级翻译阅卷老师。按 CET 翻译 15 分制评分，"
            "评分维度：信息完整度、忠实度、语法与词汇、表达流畅度。"
            "只输出合法 JSON。"
        )
        user = (
            f"考试级别：{level}\n中文原文：{prompt}\n"
            f"参考译文（可能为空）：{reference[:4000]}\n"
            f"学生译文：\n{answer}\n\n"
            "返回 JSON：{\"score_15\": 0-15 的数字, \"feedback\": \"中文总评 80-150 字\","
            "\"strengths\": [\"...\"], \"improvements\": [\"...\"],"
            "\"corrected_excerpt\": \"挑 1-2 句给出修改示例\"}。"
        )
        data = await self.chat_json(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=6000,
        )
        return self._normalize_subjective(data, "translation")

    def _normalize_subjective(self, data: dict[str, Any], kind: str) -> dict[str, Any]:
        try:
            score15 = float(data.get("score_15", 0))
        except (TypeError, ValueError):
            score15 = 0.0
        score15 = max(0.0, min(15.0, score15))
        return {
            "kind": kind,
            "score_15": round(score15, 1),
            "score_106": round(score15 / 15.0 * 106.5, 1),
            "feedback": str(data.get("feedback", "")).strip(),
            "strengths": [str(x) for x in (data.get("strengths") or [])][:5],
            "improvements": [str(x) for x in (data.get("improvements") or [])][:5],
            "corrected_excerpt": str(data.get("corrected_excerpt", "")).strip(),
        }

    def _empty_subjective(self, kind: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "score_15": 0.0,
            "score_106": 0.0,
            "feedback": "未作答，本项计 0 分。",
            "strengths": [],
            "improvements": [],
            "corrected_excerpt": "",
        }

    async def vision_text(
        self,
        images: list[bytes | Path],
        prompt: str,
        *,
        max_tokens: int = 10000,
    ) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in images:
            raw = image.read_bytes() if isinstance(image, Path) else image
            mime = "image/jpeg"
            if raw[:8] == b"\x89PNG\r\n\x1a\n":
                mime = "image/png"
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64," + base64.b64encode(raw).decode()
                    },
                }
            )
        return await self.chat(
            [{"role": "user", "content": content}],
            temperature=0,
            max_tokens=max_tokens,
        )

    async def explain_question(
        self,
        question: dict[str, Any],
        user_answer: list[str],
    ) -> str:
        prompt = (
            "你是一名耐心的大学英语四六级老师。请用中文讲解下面这道题，"
            "先指出正确答案，再逐项解释为什么对/错，最后给出一个记忆要点。\n\n"
            f"题型：{question.get('category')}\n"
            f"题目：{question.get('question')}\n"
            f"材料：{question.get('material', '')}\n"
            f"选项：{question.get('options')}\n"
            f"标准答案：{question.get('answers')}\n"
            f"学生答案：{user_answer}\n"
            f"内置解析：{question.get('explanation')}"
        )
        return await self.chat(
            [
                {"role": "system", "content": "你擅长四六级备考，讲解清晰、准确、不编造。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
        )

    async def study_plan(self, stats: dict[str, Any]) -> str:
        prompt = (
            "请根据以下四六级模考与练习数据，用中文给出 7 天复习计划。"
            "每天给出 2-3 个可执行任务，并指出最优先补强的题型。\n\n"
            f"{json.dumps(stats, ensure_ascii=False, indent=2)}"
        )
        return await self.chat(
            [
                {"role": "system", "content": "你是一名四六级备考教练。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
        )
