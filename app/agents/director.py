from pathlib import Path

from app.providers.llm.base import LLMProvider
from app.schemas.outline import StoryOutline


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "director_v1.md"


class DirectorAgent:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def generate_outline(self, idea: str, episode_count: int = 10) -> StoryOutline:
        user_prompt = (
            f"短剧创意：{idea}\n"
            f"集数：{episode_count}\n"
            "请严格按照系统提示中的 JSON 结构生成故事设定与分集大纲。"
        )
        return self._llm_provider.generate_structured(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            output_schema=StoryOutline,
        )
