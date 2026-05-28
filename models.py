"""
数据模型：用户 + 改写记录
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    # 改写历史统计
    total_rewrites = db.Column(db.Integer, default=0)
    total_chars = db.Column(db.Integer, default=0)

    # 自定义 AI API 配置（可选）
    ai_api_key = db.Column(db.String(256), default="")
    ai_api_base_url = db.Column(db.String(256), default="")
    ai_model = db.Column(db.String(64), default="")

    # 自定义 Skill Prompt（用户自定义改写提示词，优先级最高）
    custom_skill_prompt = db.Column(db.Text, default="")

    # 关联
    records = db.relationship("RewriteRecord", backref="user", lazy="dynamic",
                              order_by="RewriteRecord.created_at.desc()")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class RewriteRecord(db.Model):
    """单条改写记录"""
    __tablename__ = "rewrite_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original = db.Column(db.Text, nullable=False)
    rewritten = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(16), nullable=False, default="both")
    changes = db.Column(db.Text, default="{}")
    char_count = db.Column(db.Integer, default=0)
    title = db.Column(db.String(128), default="")
    created_at = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self, brief=False):
        """转为字典"""
        d = {
            "id": self.id,
            "mode": self.mode,
            "char_count": self.char_count,
            "title": self.title or self.original[:20] + ("..." if len(self.original) > 20 else ""),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }
        if brief:
            d["preview"] = self.original[:60] + ("..." if len(self.original) > 60 else "")
        else:
            d["original"] = self.original
            d["rewritten"] = self.rewritten
            d["changes"] = self.changes
        return d
