"""
应用配置
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

_basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(_basedir, 'thesis_rewriter.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI API 配置（可选）
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "https://api.deepseek.com/v1")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
