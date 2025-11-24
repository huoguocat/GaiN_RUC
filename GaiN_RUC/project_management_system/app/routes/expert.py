from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ..models import db
from ..models.review import Review

expert_bp = Blueprint("expert", __name__, url_prefix="/expert")


def ensure_expert():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role != "expert":
        abort(403)


@expert_bp.before_request
def expert_guard():
    if request.endpoint and request.endpoint.startswith("expert."):
        return ensure_expert()


@expert_bp.route("/dashboard")
@login_required
def dashboard():
    pending = current_user.reviews.filter_by(status="待确认").count()
    reviewing = current_user.reviews.filter_by(status="待评审").count()
    completed = current_user.reviews.filter(Review.status.in_(["已提交", "答辩完成"])).count()
    notices = [
        "请在截止前完成当前批次评审。",
        "新答辩安排将在 24 小时前推送提醒。",
    ]
    return render_template(
        "expert/dashboard.html",
        pending=pending,
        reviewing=reviewing,
        completed=completed,
        notices=notices,
    )


@expert_bp.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    if request.method == "POST":
        review_id = request.form.get("review_id")
        action = request.form.get("action")
        reason = request.form.get("reason")
        review = Review.query.filter_by(id=review_id, expert=current_user).first_or_404()
        if action == "confirm":
            review.status = "待评审"
            flash("任务已确认。", "success")
        elif action == "swap":
            review.status = "调换申请中"
            review.comments = f"【申请调换】{reason or '无理由'}"
            flash("已提交调换申请。", "info")
        db.session.commit()
        return redirect(url_for("expert.tasks"))

    status = request.args.get("status")
    query = current_user.reviews.order_by(Review.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    reviews = query.all()
    return render_template("expert/tasks.html", reviews=reviews, status=status)


@expert_bp.route("/tasks/<int:review_id>", methods=["GET", "POST"])
@login_required
def review_form(review_id):
    review = Review.query.filter_by(id=review_id, expert=current_user).first_or_404()
    if request.method == "POST":
        review.tech_score = int(request.form.get("tech_score", 0))
        review.market_score = int(request.form.get("market_score", 0))
        review.feasibility_score = int(request.form.get("feasibility_score", 0))
        review.team_score = int(request.form.get("team_score", 0))
        review.comments = request.form.get("comments")
        action = request.form.get("action")
        review.status = "暂存" if action == "draft" else "已提交"
        db.session.commit()
        flash("评审结果已保存。" if action == "draft" else "评审提交成功。", "success")
        return redirect(url_for("expert.tasks"))
    return render_template("expert/review_form.html", review=review)


@expert_bp.route("/defense/<int:review_id>", methods=["GET", "POST"])
@login_required
def defense(review_id):
    review = Review.query.filter_by(id=review_id, expert=current_user).first_or_404()
    if request.method == "POST":
        review.defense_score = int(request.form.get("defense_score", 0))
        review.defense_notes = request.form.get("defense_notes")
        review.status = "答辩完成"
        db.session.commit()
        flash("答辩意见已提交。", "success")
        return redirect(url_for("expert.history"))
    return render_template("expert/defense_form.html", review=review)


@expert_bp.route("/history")
@login_required
def history():
    reviews = (
        current_user.reviews.filter(Review.status.in_(["已提交", "答辩完成"]))
        .order_by(Review.updated_at.desc())
        .all()
    )
    return render_template("expert/history.html", reviews=reviews)

