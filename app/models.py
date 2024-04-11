from .database import db
import pytz
from datetime import datetime


class Participant(db.Model):
    __tablename__ = "participant"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(pytz.timezone("Asia/Seoul"))
    )


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer)  # ForeignKey 제거, 정수 값으로 직접 저장
    chosen_answer = db.Column(db.String(255))
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    participant = db.relationship("Participant", backref="answers")
