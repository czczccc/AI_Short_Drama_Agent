import json

from app.models.project import Project
from app.schemas.memory import (
    CharacterMemoryUpdate,
    EpisodeEndingState,
    EpisodeMemory,
    StoryMemory,
)
from app.schemas.script import EpisodeScript


def load_story_memory(project: Project) -> StoryMemory:
    if not project.memory_json:
        return _build_memory_from_saved_scripts(project)
    return StoryMemory.model_validate_json(project.memory_json)


def _build_memory_from_saved_scripts(project: Project) -> StoryMemory:
    if not project.scripts_json:
        return StoryMemory()
    scripts = json.loads(project.scripts_json)
    episodes = {}
    for episode_key in sorted(scripts, key=int):
        script = EpisodeScript.model_validate(scripts[episode_key])
        episode_memory = build_episode_memory(script)
        episodes[str(script.episode_number)] = episode_memory
    return StoryMemory(episodes=episodes)


def build_episode_memory(script: EpisodeScript) -> EpisodeMemory:
    character_scene_facts: dict[str, list[str]] = {}
    for scene in script.scenes:
        for character_id in scene.characters:
            character_scene_facts.setdefault(character_id, []).append(scene.scene_goal)

    character_updates = {}
    for character_id, scene_facts in sorted(character_scene_facts.items()):
        deduplicated_facts = list(dict.fromkeys(scene_facts))
        character_updates[character_id] = CharacterMemoryUpdate(
            knows=deduplicated_facts,
            current_goal=deduplicated_facts[-1] if deduplicated_facts else None,
        )
    return EpisodeMemory(
        episode_number=script.episode_number,
        source="rule_extracted",
        summary=script.episode_goal,
        new_facts=[scene.scene_goal for scene in script.scenes],
        revealed_secrets=[],
        unresolved_questions=[script.ending_hook],
        character_updates=character_updates,
        props_and_evidence=[],
        ending_state=EpisodeEndingState(
            location=script.scenes[-1].location,
            time_of_day=script.scenes[-1].time_of_day,
            situation=script.scenes[-1].scene_goal,
        ),
        ending_hook=script.ending_hook,
    )


def upsert_episode_memory(
    project: Project,
    script: EpisodeScript,
    approved_memory: EpisodeMemory | None = None,
) -> StoryMemory:
    memory = load_story_memory(project)
    kept_episodes = {
        episode_key: episode
        for episode_key, episode in memory.episodes.items()
        if episode.episode_number < script.episode_number
    }
    if (
        approved_memory is not None
        and approved_memory.episode_number != script.episode_number
    ):
        raise ValueError("approved_memory 与剧本集号不一致")
    if approved_memory is not None and approved_memory.source != "qc_approved":
        raise ValueError("approved_memory 的 source 必须为 qc_approved")
    episode_memory = approved_memory or build_episode_memory(script)
    kept_episodes[str(script.episode_number)] = episode_memory
    updated_memory = StoryMemory(episodes=kept_episodes)
    project.memory_json = json.dumps(
        updated_memory.model_dump(mode="json"),
        ensure_ascii=False,
    )
    return updated_memory
