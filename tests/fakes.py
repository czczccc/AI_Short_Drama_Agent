from typing import TypeVar

from pydantic import BaseModel

from app.schemas.character import CharacterBible, CharacterBibleCollection
from app.schemas.outline import StoryOutline
from app.schemas.qc import QCReport
from app.schemas.script import EpisodeScript
from app.schemas.showrunner import ShowrunnerState


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
    duration_seconds: int = 90,
) -> dict:
    return {
        "episode_number": episode_number,
        "title": title or f"第{episode_number}集AI证据争夺战",
        "duration_seconds": duration_seconds,
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


def valid_qc_report_data(episode_number: int = 1) -> dict:
    return {
        "episode_number": episode_number,
        "status": "warning",
        "summary": "整体可用，但存在一个可能提前展开后续线索的问题。",
        "issues": [
            {
                "episode_number": episode_number,
                "severity": "warning",
                "code": "future_boundary_risk",
                "message": "剧本结尾可能提前揭示后续集才应确认的关键证据结果。",
                "suggestion": "保留发现证据的悬念，不要在本集确认最终结论。",
            }
        ],
    }


def valid_showrunner_state_data(
    source_outline_hash: str | None = None,
    source_characters_hash: str | None = None,
) -> dict:
    outline = valid_outline_data()
    characters = valid_character_bibles_data()
    return {
        "version": "showrunner_v1",
        "source_outline_hash": source_outline_hash
        or "0" * 64,
        "source_characters_hash": source_characters_hash
        or "1" * 64,
        "story_bible": {
            "series_title": outline["title"],
            "logline": outline["logline"],
            "genre": outline["genre"],
            "tone": outline["tone"],
            "world_rules": ["故事发生在当代中国人工智能创业语境中。"],
            "canon_facts": ["林峰被开除后发现老板窃取了他的AI成果。"],
            "core_conflict": outline["core_conflict"],
            "main_mysteries": ["关键证据为何被持续销毁。"],
            "forbidden_reveals": ["不得在前期提前确认最终证据结果。"],
            "continuity_rules": ["每集只能展开该集大纲范围内的核心事件。"],
        },
        "episode_plan": [
            {
                "episode_number": episode["episode_number"],
                "title": episode["title"],
                "dramatic_function": f"推进第{episode['episode_number']}集调查压力。",
                "must_include": [episode["summary"]],
                "must_not_reveal": ["不得提前完成后续集的最终反转。"],
                "setup": [episode["main_conflict"]],
                "payoff": [f"兑现第{episode['episode_number']}集的阶段性冲突。"],
                "ending_hook": episode["ending_hook"],
                "allowed_new_facts": [episode["summary"]],
            }
            for episode in outline["episodes"]
        ],
        "character_arcs": [
            {
                "character_id": character_id,
                "character_name": bible["name"],
                "starting_state": f"{bible['name']}开局被核心冲突牵引。",
                "ending_state": f"{bible['name']}季末必须完成与动机相关的选择。",
                "episode_beats": [
                    {
                        "episode_number": number,
                        "emotional_state": "紧张克制",
                        "goal": f"完成第{number}集中的人物目标。",
                        "change": f"在第{number}集中获得阶段性变化。",
                        "knowledge_state": f"只知道第{number}集及之前已经发生的信息。",
                    }
                    for number in range(1, 11)
                ],
            }
            for character_id, bible in characters.items()
        ],
        "writer_briefs": {},
        "qc_reports": {},
    }


class FakeLLMProvider:
    def __init__(
        self,
        script_episode_number: int = 1,
        script_title: str | None = None,
        script_character_id: str = "lin_feng",
        script_duration_seconds: int = 90,
        character_mode: str = "valid",
        showrunner_mode: str = "valid",
        script_dialogue_key: str = "dialogues",
    ) -> None:
        self.script_episode_number = script_episode_number
        self.script_title = script_title
        self.script_character_id = script_character_id
        self.script_duration_seconds = script_duration_seconds
        self.character_mode = character_mode
        self.showrunner_mode = showrunner_mode
        self.script_dialogue_key = script_dialogue_key
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[SchemaT],
    ) -> SchemaT:
        assert "JSON" in system_prompt
        assert user_prompt.strip()
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if output_schema is StoryOutline:
            return output_schema.model_validate(valid_outline_data())
        if output_schema is CharacterBibleCollection:
            characters = valid_character_bibles_data()
            if self.character_mode == "add":
                characters["new_person"] = {
                    **characters["lin_feng"],
                    "character_id": "new_person",
                    "name": "新增人物",
                }
            if self.character_mode == "drop":
                characters.pop("gao_qi")
                return output_schema.model_construct(
                    characters={
                        character_id: CharacterBible.model_validate(bible)
                        for character_id, bible in characters.items()
                    }
                )
            return output_schema.model_validate({"characters": characters})
        if output_schema is EpisodeScript:
            script_data = valid_script_data(
                episode_number=self.script_episode_number,
                title=self.script_title,
                character_id=self.script_character_id,
                duration_seconds=self.script_duration_seconds,
            )
            if self.script_dialogue_key == "dialogue":
                for scene in script_data["scenes"]:
                    scene["dialogue"] = scene.pop("dialogues")
            return output_schema.model_validate(script_data)
        if output_schema is QCReport:
            return output_schema.model_validate(
                valid_qc_report_data(self.script_episode_number)
            )
        if output_schema is ShowrunnerState:
            data = valid_showrunner_state_data(
                source_outline_hash="0" * 64,
                source_characters_hash="1" * 64,
            )
            if self.showrunner_mode == "add_arc":
                data["character_arcs"].append(
                    {
                        **data["character_arcs"][0],
                        "character_id": "new_person",
                        "character_name": "新增人物",
                    }
                )
            if self.showrunner_mode == "drop_arc":
                data["character_arcs"].pop()
            return output_schema.model_validate(
                data
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

