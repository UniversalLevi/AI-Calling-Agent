from typing import List, Dict

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL, SYSTEM_PROMPT


class GPTBrain:
    def __init__(self) -> None:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "REPLACE_ME":
            raise RuntimeError("OPENAI_API_KEY is missing. Please set it in .env")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        completion = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=self.history,
            temperature=0.6,
        )
        reply = completion.choices[0].message.content or ""
        self.history.append({"role": "assistant", "content": reply})
        return reply.strip()


