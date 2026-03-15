from datetime import datetime, timedelta, UTC
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user

from vcesim.models.exam import Exam, Section, Question, Option, ExamAttempt, Answer
from vcesim.ui import db

student_bp = Blueprint("student_bp", __name__,
                        template_folder="templates",
                        static_folder="../static")

@student_bp.route("/dashboard")
@login_required
def dashboard():
    exams = Exam.query.all()
    attempts = ExamAttempt.query.filter_by(
        user_id=current_user.id
    ).order_by(
        ExamAttempt.started_at.desc()
    ).all()

    return render_template("student/dashboard.html",
                           exams=exams, attempts=attempts)

@student_bp.route("/exam/<int:exam_id>/start", methods=['GET', 'POST'])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == "POST":
        mode = request.form.get("mode")
        is_timed = True if mode == "timed" else False
        attempt = ExamAttempt(
            user_id = current_user.id,
            exam_id = exam.id,
            started_at = datetime.now(UTC),
            is_timed = is_timed
        )
        db.session.add(attempt)
        db.session.commit()

        session["exam_state"] = {
            "attempt_id": attempt.id,
            "current_question": 0,
            "answers": {},
            "flagged": [],
            "start_time": datetime.now(UTC).isoformat(),
            "time_limit": exam.time_limit
        }

        return redirect(url_for('student_bp.take_question',
                                attempt_id=attempt.id,
                                question_index=0
                                ))
    return render_template("exam/start_exam.html", exam=exam)

@student_bp.route("/attempt/<int:attempt_id>/question/<int:question_index>", methods=['GET', 'POST'])
@login_required
def take_question(attempt_id, question_index):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = Exam.query.get_or_404(attempt.exam_id)
    #Calculate remaining time
    remaining_time = None
    if attempt.is_timed:
        end_time = attempt.started_at + timedelta(minutes=exam.time_limit)
        remaining_time = int((end_time - datetime.now(UTC)).total_seconds())
        if remaining_time <= 0:
            return redirect(url_for("student_bp.submit_exam", attempt_id=attempt.id))
    #Gather all questions
    questions = []
    for section in exam.sections:
        questions.extend(section.questions)
    if question_index < 0:
        question_indx = 0
    if question_index >= len(questions):
        return redirect(url_for("student_bp.review_exam", attempt_id=attempt.id))
    question = questions[question_index]
    #Get options for this questions
    selected_answers = [
        a.selected_option_id
        for a in attempt.answers
        if a.question_id == question.id and a.selected_option_id
    ]
    # Get flagged state
    flagged = any(
        a.flagged for a in attempt.answers
        if a.question_id == question.id
    )

    if request.method == "POST":
        # Remove old answers for this question
        Answer.query.filter_by(
            attempt_id=attempt.id,
            question_id=question.id
        ).delete()
        selected_options = request.form.getlist("options")
        is_flagged = request.form.get("flag") == "on"
        # Remove old answers
        Answer.query.filter_by(
            attempt_id=attempt.id,
            question_id=question.id
        ).delete()
        for option_id in selected_options:
            answer = Answer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=int(option_id),
                flagged=is_flagged
            )
            db.session.add(answer)
        # if flagged, but no options selected
        if not selected_options and is_flagged:
            answer = Answer(
                attempt_id=attempt.id,
                question_id=question.id,
                flagged=True
            )
            db.session.add(answer)
        db.session.commit()
        return redirect(url_for("student_bp.take_question",
                                attempt_id=attempt.id,
                                question_index=question_index + 1))
    return render_template("exam/question.html",
                           attempt=attempt,
                           question=question,
                           question_index=question_index,
                           total=len(questions),
                           questions=questions,
                           remaining_time=remaining_time,
                           selected_answers=selected_answers,
                           flagged=flagged
                           )

@student_bp.route("/attempt/<int:attempt_id>/submit")
@login_required
def submit_exam(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = Exam.query.get_or_404(attempt.exam_id)
    if attempt.is_timed:
        end_time = attempt.started_at + timedelta(minutes=exam.time_limit)
        if datetime.now(UTC) > end_time:
            attempt.completed_at = end_time
        else:
            attempt.completed_at = datetime.now(UTC)
    else:
        attempt.completed_at = datetime.now(UTC)
        
    questions = []
    for section in exam.sections:
        questions.extend(section.questions)

    correct_count = 0

    for question in questions:
        correct_options = {o.id for o in question.options if o.is_correct}
        selected_options = {
            a.selected_option_id
            for a in attempt.answers
            if a.question_id == question.id
        }

        if correct_options == selected_options:
            correct_count += 1

    raw_score = correct_count / len(questions) if questions else 0
    scaled_score = int(100 + raw_score * 900)

    attempt.score = scaled_score
    attempt.passed = scaled_score >= exam.passing_score
    attempt.completed_at = datetime.utcnow()

    db.session.commit()

    return redirect(url_for("student_bp.results", attempt_id=attempt.id))

@student_bp.route("/results/<int:attempt_id>")
@login_required
def results(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = Exam.query.get_or_404(attempt.exam_id)

    return render_template(
        "exam/results.html",
        attempt=attempt,
        exam=exam
    )

@student_bp.route("/attempt/<int:attempt_id>/review")
@login_required
def review_exam(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = Exam.query.get_or_404(attempt.exam_id)

    questions = []
    for section in exam.sections:
        questions.extend(section.questions)

    return render_template(
        "exam/review.html",
        attempt=attempt,
        questions=questions
    )

@student_bp.route("/attempt/<int:attempt_id>/reveal/<int:question_id>")
@login_required
def reveal_answer(attempt_id, question_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)

    # Only allowed in untimed mode
    if attempt.is_timed:
        return redirect(url_for("student.take_question",
                                attempt_id=attempt.id,
                                question_index=0))

    question = Question.query.get_or_404(question_id)

    return render_template(
        "exam/reveal.html",
        attempt=attempt,
        question=question
    )
