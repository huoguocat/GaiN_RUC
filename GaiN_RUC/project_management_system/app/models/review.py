from datetime import datetime

from . import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(40), default="待确认")
    tech_score = db.Column(db.Integer, default=0)
    market_score = db.Column(db.Integer, default=0)
    feasibility_score = db.Column(db.Integer, default=0)
    team_score = db.Column(db.Integer, default=0)
    defense_score = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text)
    defense_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    project = db.relationship("Project", back_populates="reviews")
    expert = db.relationship("User", back_populates="reviews")

    def overall_score(self) -> float:
        return (
            self.tech_score
            + self.market_score
            + self.feasibility_score
            + self.team_score
            + self.defense_score
        ) / 5

    def __repr__(self) -> str:
        return f"<Review project={self.project_id} expert={self.expert_id}>"

