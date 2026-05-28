"""
毕业论文降重降AI网站 - Flask应用主入口
"""
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, RewriteRecord
from services.rewriter import ThesisRewriter

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# --- 登录管理器 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "请先登录后再使用"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --- 初始化数据库 ---
with app.app_context():
    db.create_all()
    # 迁移：为已有表添加新字段（如不存在）
    import sqlalchemy as sa
    inspector = sa.inspect(db.engine)
    
    # 迁移 users 表
    users_cols = [c["name"] for c in inspector.get_columns("users")]
    for col in ("ai_api_key", "ai_api_base_url", "ai_model"):
        if col not in users_cols:
            db.session.execute(sa.text(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT ''"))
    
    # 迁移 rewrite_records 表
    records_cols = [c["name"] for c in inspector.get_columns("rewrite_records")]
    if "title" not in records_cols:
        db.session.execute(sa.text("ALTER TABLE rewrite_records ADD COLUMN title TEXT DEFAULT ''"))
    
    # 迁移 users 表：custom_skill_prompt
    if "custom_skill_prompt" not in users_cols:
        db.session.execute(sa.text("ALTER TABLE users ADD COLUMN custom_skill_prompt TEXT DEFAULT ''"))

    db.session.commit()


def get_rewriter():
    """获取改写器实例（优先使用用户自定义配置 + 自定义Skill prompt）"""
    api_key = current_user.ai_api_key or app.config.get("AI_API_KEY") or None
    api_base_url = current_user.ai_api_base_url or app.config.get("AI_API_BASE_URL")
    api_model = current_user.ai_model or app.config.get("AI_MODEL")
    custom_prompt = current_user.custom_skill_prompt or ""

    return ThesisRewriter(
        api_key=api_key,
        api_base_url=api_base_url,
        api_model=api_model,
        custom_prompt=custom_prompt,
    )


# =============================================
#  登录 / 注册 / 注销
# =============================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("请输入用户名和密码", "warning")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("用户名或密码错误", "error")
            return render_template("login.html")

        login_user(user)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = []
        if not username or len(username) < 2:
            errors.append("用户名至少2个字符")
        if not email or "@" not in email:
            errors.append("请输入有效的邮箱地址")
        if len(password) < 6:
            errors.append("密码至少6位")
        if password != confirm:
            errors.append("两次密码输入不一致")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "warning")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("邮箱已被注册", "warning")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("注册成功，请登录", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    """注销"""
    logout_user()
    return redirect(url_for("index"))


# =============================================
#  核心功能（需登录）
# =============================================

@app.route("/")
@login_required
def index():
    """首页"""
    return render_template("index.html", has_api=bool(app.config.get("AI_API_KEY")))


@app.route("/rewrite", methods=["POST"])
@login_required
def rewrite():
    """处理改写请求（自动保存历史）"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求数据为空"}), 400

    text = data.get("text", "").strip()
    if not text:
        return jsonify({"success": False, "error": "请输入论文文本"}), 400

    if len(text) > 50000:
        return jsonify({"success": False, "error": "文本过长，请控制在50000字以内"}), 400

    mode = data.get("mode", "both")
    if mode not in ("reduce", "deai", "both"):
        return jsonify({"success": False, "error": "无效的处理模式"}), 400

    try:
        rewriter = get_rewriter()
        result = rewriter.rewrite(text, mode=mode)

        # 更新用户统计
        current_user.total_rewrites += 1
        current_user.total_chars += len(text)

        # 保存到历史记录
        title = text[:30] + ("..." if len(text) > 30 else "")
        record = RewriteRecord(
            user_id=current_user.id,
            original=result["original"],
            rewritten=result["rewritten"],
            mode=mode,
            changes=json.dumps(result["changes"], ensure_ascii=False),
            char_count=len(text),
            title=title,
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "success": True,
            "record_id": record.id,
            "original": result["original"],
            "rewritten": result["rewritten"],
            "changes": result["changes"],
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"处理失败：{str(e)}"}), 500


# =============================================
#  历史记录 API
# =============================================

@app.route("/api/history")
@login_required
def list_history():
    """获取当前用户的历史记录列表（分页）"""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)

    pagination = RewriteRecord.query \
        .filter_by(user_id=current_user.id) \
        .order_by(RewriteRecord.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "records": [r.to_dict(brief=True) for r in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@app.route("/api/history/<int:record_id>")
@login_required
def get_history(record_id):
    """获取单条历史记录详情"""
    record = RewriteRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"success": False, "error": "记录不存在"}), 404

    return jsonify({
        "success": True,
        "record": record.to_dict(brief=False),
    })


@app.route("/api/history/<int:record_id>/rename", methods=["POST"])
@login_required
def rename_history(record_id):
    """重命名历史记录"""
    record = RewriteRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"success": False, "error": "记录不存在"}), 404

    data = request.get_json()
    new_title = (data.get("title") or "").strip()
    if not new_title:
        return jsonify({"success": False, "error": "标题不能为空"}), 400
    if len(new_title) > 100:
        return jsonify({"success": False, "error": "标题过长"}), 400

    record.title = new_title
    db.session.commit()
    return jsonify({"success": True, "title": new_title})


@app.route("/api/history/<int:record_id>", methods=["DELETE"])
@login_required
def delete_history(record_id):
    """删除单条历史记录"""
    record = RewriteRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"success": False, "error": "记录不存在"}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"success": True})


# =============================================
#  对比页面（支持历史记录 ID）
# =============================================

@app.route("/compare")
@login_required
def compare():
    """对比页面（优先从 record_id 加载）"""
    record_id = request.args.get("record_id", type=int)

    if record_id:
        record = RewriteRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
        if record:
            return render_template("result.html",
                                   original=record.original,
                                   rewritten=record.rewritten,
                                   changes=record.changes,
                                   record_id=record.id)

    # 后备：从 URL 参数加载
    original = request.args.get("original", "")
    rewritten = request.args.get("rewritten", "")
    return render_template("result.html", original=original, rewritten=rewritten,
                           changes="{}", record_id=None)


# =============================================
#  设置页面（自定义 API 配置）
# =============================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """设置页面 - 自定义 AI 模型 API + 自定义 Skill"""
    if request.method == "POST":
        api_key = request.form.get("api_key", "").strip()
        api_base_url = request.form.get("api_base_url", "").strip()
        api_model = request.form.get("api_model", "").strip()
        custom_skill = request.form.get("custom_skill", "").strip()

        current_user.ai_api_key = api_key
        current_user.ai_api_base_url = api_base_url
        current_user.ai_model = api_model
        current_user.custom_skill_prompt = custom_skill
        db.session.commit()
        flash("设置已保存", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html",
                           api_key=current_user.ai_api_key or "",
                           api_base_url=current_user.ai_api_base_url or "",
                           api_model=current_user.ai_model or "",
                           custom_skill_prompt=current_user.custom_skill_prompt or "")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
