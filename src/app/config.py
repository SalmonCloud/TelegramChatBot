from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

# 假设路径为 src/app/config.py
# parents[2] = 项目根目录
ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"                # 项目根/.env
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """
    SalmonCloud Telegram bridge bot 配置
    """

    # === Telegram 相关 ===
    api_id: int = Field(validation_alias=AliasChoices("API_ID"))
    api_hash: str = Field(validation_alias=AliasChoices("API_HASH"))
    bot_token: str = Field(validation_alias=AliasChoices("BOT_TOKEN"))
    internal_group_id: int = Field(validation_alias=AliasChoices("INTERNAL_GROUP_ID"))
    internal_topic_id: int = Field(validation_alias=AliasChoices("INTERNAL_TOPIC_ID"))

    # === MySQL 数据库配置 ===
    db_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("DB_HOST"),
    )
    db_port: int = Field(
        default=3306,
        validation_alias=AliasChoices("DB_PORT"),
    )
    db_name: str = Field(
        default="ChatBot",
        validation_alias=AliasChoices("DB_NAME"),
    )
    db_user: str = Field(
        validation_alias=AliasChoices("DB_USER"),
    )
    db_password: str = Field(
        validation_alias=AliasChoices("DB_PASSWORD"),
    )

    # 可选：如果你想本地试试 SQLite，可以用这个 db_path；当前代码没用到，但保留不冲突
    db_path: str = Field(
        default=str(DATA_DIR / "bot.db"),
        validation_alias=AliasChoices("DB_PATH"),
    )

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 兼容写法：from app.config import settings
settings: Settings = get_settings()
