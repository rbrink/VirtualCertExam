from datetime import datetime

from vcesim.models.user import User
from vcesim.ui import db

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="Untitled Exam")
    number = db.Column(db.String(50), default="000-0000")
    version = db.Column(db.String(20), default="1.0")
    passing_score = db.Column(db.Integer, default=800)
    time_limit = db.Column(db.Integer, default=120)
    description = db.Column(db.Text)

    sections = db.relationship("Section", backref="exam", cascade="all, delete")

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))

    questions = db.relationship("Question", backref="section", cascade="all, delete")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    is_multi_answer = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(100))
    explanation = db.Column(db.Text)
    complexity = db.Column(db.Integer, default=1)
    section_id = db.Column(db.Integer, db.ForeignKey("section.id"))

    options = db.relationship("Option", backref="question", cascade="all, delete")

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    passed = db.Column(db.Boolean)
    percent = db.Column(db.Float)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_timed = db.Column(db.Boolean, default=True)
    mode = db.Column(db.String(10))

    user = db.relationship("User", backref="attempts")
    exam = db.relationship("Exam")
    answers = db.relationship("Answer", backref="attempt", cascade="all, delete")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("exam_attempt.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"))
    selected_option_id = db.Column(db.Integer, db.ForeignKey("option.id"))
    flagged = db.Column(db.Boolean, default=False)

    question = db.relationship("Question")
    option = db.relationship("Option")

class QuestionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("exam_attempt.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    is_correct = db.Column(db.Boolean)
    time_spent = db.Column(db.Integer, default=0)  # seconds
    flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempt = db.relationship("ExamAttempt", backref="question_attempts")
    question = db.relationship("Question")
