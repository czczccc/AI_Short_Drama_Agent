import pytest

from tools.text_eval_runner import episode_window


def test_episode_window_supports_second_half_of_ten_episode_season() -> None:
    assert episode_window(6, 10) == [6, 7, 8, 9, 10]


@pytest.mark.parametrize(
    ("start_episode", "end_episode"),
    [(0, 5), (1, 11), (6, 5)],
)
def test_episode_window_rejects_invalid_bounds(
    start_episode: int,
    end_episode: int,
) -> None:
    with pytest.raises(ValueError):
        episode_window(start_episode, end_episode)
