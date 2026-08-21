"""PPO(Stable-Baselines3) 학습 진입점. 페어/호가 스프레드 환경 공용."""
from __future__ import annotations

from pathlib import Path

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv


def train_ppo(
    env_factory,
    total_timesteps: int = 200_000,
    model_out_path: str | Path = "models/ppo_model.zip",
    tensorboard_log: str | Path | None = "logs/tensorboard",
    **ppo_kwargs,
) -> PPO:
    """
    Args:
        env_factory: () -> gym.Env 를 반환하는 콜러블 (PairSpreadEnv/QuoteSpreadEnv 인스턴스 생성용).
        total_timesteps: 총 학습 스텝 수.
        model_out_path: 학습 완료 후 저장할 경로.
        ppo_kwargs: PPO 생성자에 전달할 추가 하이퍼파라미터.
    """

    def _make() -> gym.Env:
        return Monitor(env_factory())

    vec_env = DummyVecEnv([_make])

    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        tensorboard_log=str(tensorboard_log) if tensorboard_log else None,
        **ppo_kwargs,
    )
    model.learn(total_timesteps=total_timesteps)

    out_path = Path(model_out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    return model
