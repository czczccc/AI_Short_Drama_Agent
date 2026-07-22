from typing import TypeVar

from pydantic import BaseModel

from app.schemas.outline import StoryOutline
from app.schemas.script import EpisodeScript


SchemaT = TypeVar("SchemaT", bound=BaseModel)


def valid_outline_data() -> dict:
    return {
        "title": "逆光代码",
        "logline": "被开除的程序员发现老板窃取成果，决定夺回真相。",
        "genre": "都市悬疑",
        "tone": "紧张热血",
        "target_audience": "年轻职场观众",
        "world_setting": "当代中国人工智能创业公司。",
        "core_conflict": "程序员必须在资本封锁下证明成果归属。",
        "themes": ["职场正义", "技术伦理"],
        "characters": [
            {
                "character_id": "lin_feng",
                "name": "林峰",
                "role": "男主角",
                "age": "二十八岁",
                "appearance": "清瘦干练，常穿旧夹克。",
                "personality": "克制执着，善于推理。",
                "motivation": "夺回成果并证明清白。",
                "secret": "保留了算法最早的离线记录。",
            },
            {
                "character_id": "su_yan",
                "name": "苏妍",
                "role": "调查记者",
                "age": "二十七岁",
                "appearance": "利落短发，目光敏锐。",
                "personality": "果断正直，不惧压力。",
                "motivation": "揭开科技公司的造假内幕。",
                "secret": "她的父亲曾被同一老板陷害。",
            },
            {
                "character_id": "gao_qi",
                "name": "高启",
                "role": "反派老板",
                "age": "四十二岁",
                "appearance": "衣着考究，笑容冷淡。",
                "personality": "精明强势，控制欲极强。",
                "motivation": "保住融资与行业地位。",
                "secret": "核心演示数据同样是伪造的。",
            },
        ],
        "episodes": [
            {
                "episode_number": number,
                "title": f"第{number}集反击",
                "summary": f"林峰推进第{number}步调查并逼近真相。",
                "main_conflict": "林峰的证据遭到高启阻挠。",
                "ending_hook": f"一份关键记录突然显示第{number}个秘密。",
            }
            for number in range(1, 11)
        ],
    }


def valid_script_data(
    episode_number: int = 1,
    title: str | None = None,
    character_id: str = "lin_feng",
) -> dict:
    return {
        "episode_number": episode_number,
        "title": title or f"第{episode_number}集AI证据争夺战",
        "duration_seconds": 90,
        "episode_goal": "林峰必须抢在高启之前取得服务器证据。",
        "opening_hook": "开场五秒内，林峰的电脑突然开始远程自毁。",
        "scenes": [
            {
                "scene_number": number,
                "location": "人工智能公司机房",
                "time_of_day": "深夜",
                "characters": [character_id],
                "scene_goal": f"完成第{number}步取证。",
                "action": "警报声逼近，林峰迅速复制关键文件。",
                "dialogues": [
                    {
                        "character_id": character_id,
                        "character_name": "林峰",
                        "emotion": "紧张",
                        "line": "只剩十秒，必须拿到证据！",
                        "action_note": "手指飞快敲击键盘。",
                    }
                ],
                "transition": "画面切向不断缩短的倒计时。",
            }
            for number in range(1, 4)
        ],
        "ending_hook": "文件打开后，屏幕上竟出现苏妍父亲的名字。",
    }


def valid_character_bibles_data() -> dict:
    concepts = valid_outline_data()["characters"]
    target_ids = {
        "lin_feng": "su_yan",
        "su_yan": "gao_qi",
        "gao_qi": "lin_feng",
    }
    return {
        concept["character_id"]: {
            "character_id": concept["character_id"],
            "name": concept["name"],
            "role": concept["role"],
            "age": concept["age"],
            "background": f"{concept['name']}长期身处人工智能行业核心冲突之中。",
            "appearance": concept["appearance"],
            "personality": concept["personality"],
            "motivation": concept["motivation"],
            "fear": "害怕关键真相被永久掩盖。",
            "secret": concept["secret"],
            "speech_style": "说话简短克制，面对压力时仍保持清晰判断。",
            "behavior_patterns": ["遇到冲突先观察证据，再采取行动。"],
            "emotional_triggers": ["发现重要证据被恶意销毁时会明显愤怒。"],
            "behavior_boundaries": ["不会为了胜利主动伤害无辜者。"],
            "relationships": [
                {
                    "target_character_id": target_ids[concept["character_id"]],
                    "relationship_type": "剧情关键关系",
                    "public_attitude": "公开保持克制和必要距离。",
                    "private_attitude": "内心持续评估对方是否值得信任。",
                    "conflict": "双方对真相和利益的选择存在直接冲突。",
                }
            ],
            "character_arc": "从独自承担压力逐步学会信任同伴并直面真相。",
            "visual_identity": {
                "face_features": "面部轮廓清晰，目光具有辨识度。",
                "hair": "保持利落整洁的日常发型。",
                "body_type": "身形匀称，动作干练。",
                "default_costume": "默认穿深色简洁职业装。",
                "signature_colors": "以深蓝和灰色作为主要识别色。",
                "signature_props": "随身携带具有剧情意义的旧机械表。",
            },
            "continuity_rules": {
                "must_keep": ["始终保持核心动机和表达方式一致。"],
                "must_avoid": ["不使用与人物身份不符的网络流行语。"],
            },
        }
        for concept in concepts
    }


class FakeLLMProvider:
    def __init__(
        self,
        script_episode_number: int = 1,
        script_title: str | None = None,
        script_character_id: str = "lin_feng",
    ) -> None:
        self.script_episode_number = script_episode_number
        self.script_title = script_title
        self.script_character_id = script_character_id

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
    ) -> SchemaT:
        assert "JSON" in system_prompt
        assert user_prompt.strip()
        if output_schema is StoryOutline:
            return output_schema.model_validate(valid_outline_data())
        if output_schema is EpisodeScript:
            return output_schema.model_validate(
                valid_script_data(
                    episode_number=self.script_episode_number,
                    title=self.script_title,
                    character_id=self.script_character_id,
                )
            )
        raise AssertionError(f"Unsupported output schema: {output_schema}")


class FailingLLMProvider:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
    ) -> SchemaT:
        raise self.error

