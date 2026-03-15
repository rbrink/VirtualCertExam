import secrets
from flask import Blueprint, render_template, redirect, url_for, request, \
    flash, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from vcesim.models.exam import Exam, Section, Question, Option, Answer, \
    ExamAttempt, QuestionAttempt
from vcesim.models.user import User
from vcesim.ui import app, db
from vcesim.ui.forms import CreateExam, QuestionForm
from vcesim.ui.utils import admin_required

admin_bp = Blueprint("admin_bp", __name__,
                     template_folder="templates",
                     static_folder="../static")

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_exams = Exam.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_exam_attempts = ExamAttempt.query.count()

    avg_score = db.session.query(
        func.avg(ExamAttempt.percent)
    ).scalar() or 0

    recent_exam_attempts = (
        ExamAttempt.query.order_by(
            ExamAttempt.started_at.desc()
        ).limit(10).all()
    )

    hardest_questions = (
        db.session.query(
            Question.question_text,
            func.avg(QuestionAttempt.is_correct.cast(db.Integer)).label("accuracy")
        ).join(QuestionAttempt).group_by(Question.id).order_by("accuracy")
        .limit(5).all()
    )

    return render_template("admin/dashboard.html", total_students=total_students,
                           total_exams=total_exams, total_exam_attempts=total_exam_attempts,
                           avg_score=round(avg_score, 2), recent_exam_attempts=recent_exam_attempts,
                           hardest_questions=hardest_questions)

@admin_bp.route("/exams")
@login_required
@admin_required
def list_exams():
    exams=Exam.query.all()
    return render_template("exam/exams.html", exams=exams)

@admin_bp.route("/exams/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_exam():
    form = CreateExam()
    if form.validate_on_submit():
        exam = Exam(
            title=form.title.data.strip(),
            number=form.exam_number.data,
            version=form.version.data.strip(),
            passing_score=form.passing_score.data,
            time_limit=form.time_limit.data,
            description=form.description.data.strip(),
        )
        db.session.add(exam)
        db.session.commit()

        app.logger.info(f"Exam {exam.title} created successfully")
        flash("Exam created successfully.", "success")
        return redirect(url_for("admin_bp.list_exams"))

    return render_template("exam/exam_form.html", exam=None, form=form)

@admin_bp.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    form = CreateExam(obj=exam)
    if form.validate_on_submit():
        exam.title = form.title.data.strip()
        exam.number = form.exam_number.data.strip()
        exam.version = form.version.data.strip()
        exam.passing_score = form.passing_score.data
        exam.time_limit = form.time_limit.data
        exam.description = form.description.data.strip()

        db.session.commit()
        app.logger.info(f"Exam {exam.title} updated successfully")
        flash("Exam updated successfully.", "success")
        return redirect(url_for("admin_bp.list_exams"))

    return render_template("exan/exam_form.html", exam=exam, form=form)

@admin_bp.route("/exams/<int:exam_id>/delete")
@login_required
@admin_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    app.logger.info(f"Exam {exam.title} deleted")
    flash("Exam deleted.", "danger")
    return redirect(url_for("admin_bp.list_exams"))

@admin_bp.route("/exams/<int:exam_id>/sections")
@login_required
@admin_required
def manage_sections(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    sections = Section.query.filter_by(exam_id=exam.id).all()

    return render_template(
        "exam/sections.html",
        exam=exam,
        sections=sections
    )

@admin_bp.route("/exams/<int:exam_id>/sections/create", methods=["POST"])
@login_required
@admin_required
def create_section(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    name = request.form["name"]

    section = Section(name=name, exam_id=exam.id)

    db.session.add(section)
    db.session.commit()

    app.logger.info(f"Section {section.name} added.")
    flash("Section added.", "success")
    return redirect(url_for("admin_bp.manage_sections", exam_id=exam.id))

@admin_bp.route("/sections/<int:section_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)

    section.name = request.form["name"]
    db.session.commit()
    app.logger.info(f"Section {section.name} updated.")
    flash("Section updated.", "success")
    return redirect(url_for("admin_bp.manage_sections", exam_id=section.exam_id))

@admin_bp.route("/sections/<int:section_id>/delete")
@login_required
@admin_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    exam_id = section.exam_id

    db.session.delete(section)
    db.session.commit()
    app.logger.info(f"Section {section.name} deleted.")
    flash("Section deleted.", "danger")
    return redirect(url_for("admin_bp.manage_sections", exam_id=exam_id))

@admin_bp.route("/sections/<int:section_id>/questions")
@login_required
@admin_required
def manage_questions(section_id):
    section = Section.query.get_or_404(section_id)
    questions = Question.query.filter_by(section_id=section.id).all()

    return render_template(
        "exam/questions.html",
        section=section,
        questions=questions
    )

@admin_bp.route("/sections/<int:section_id>/questions/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_question(section_id):
    section = Section.query.get_or_404(section_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            question_text=form.question_text.data.strip(),
            is_multi_answer=form.is_multianswer.data,
            category=form.category.data,
            complexity=form.complexity.data,
            explanation=form.explanation.data.strip(),
            section_id=section.id,
        )

        db.session.add(question)
        db.session.commit()

        # Create Options
        for i in range(1, 5):
            text = request.form.get(f"option_{i}")
            if text:
                option = Option(
                    text=text,
                    is_correct=(f"correct_{i}" in request.form),
                    question_id=question.id,
                )
                db.session.add(option)

        db.session.commit()
        app.logger.info(f"Questin {question.id} created for {section.name}")
        flash("Question created.", "success")
        return redirect(url_for("admin_bp.manage_questions", section_id=section.id))

    return render_template("exam/question_form.html", section=section, question=None, form=form)

@admin_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)
    if form.validate_on_submit():
        question.question_text = form.question_text.data.strip()
        question.is_multi_answer = form.is_multianswer.data
        question.category = form.category.data
        question.complexity = form.complexity.data
        question.explanation = form.explanation.data.strip()

        # Clear old options
        Option.query.filter_by(question_id=question.id).delete()

        for i in range(1, 5):
            text = request.form.get(f"option_{i}")
            if text:
                option = Option(
                    text=text,
                    is_correct=(f"correct_{i}" in request.form),
                    question_id=question.id,
                )
                db.session.add(option)

        db.session.commit()
        app.logger.info(f"Question {question.id} updated.")
        flash("Question updated.", "success")
        return redirect(url_for("admin_bp.manage_questions", section_id=question.section_id))

    return render_template("exam/question_form.html", section=question.section,
                           question=question, form=form)

@admin_bp.route("/questions/<int:question_id>/delete")
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    section_id = question.section_id

    db.session.delete(question)
    db.session.commit()
    app.logger.info(f"Question {question.id} deleted.")
    flash("Question deleted.", "danger")
    return redirect(url_for("admin_bp.manage_questions", section_id=section_id))

@admin_bp.route("/attempts")
@login_required
@admin_required
def view_attempts():

    if current_user.role != "admin":
        abort(403)

    attempts = ExamAttempt.query.order_by(
        ExamAttempt.start_time.desc()
    ).all()

    return render_template(
        "exam/attempts.html",
        attempts=attempts
    )

@admin_bp.route("/attempt/<int:attempt_id>")
@login_required
@admin_required
def review_attempt(attempt_id):

    if current_user.role != "admin":
        abort(403)

    attempt = ExamAttempt.query.get_or_404(attempt_id)

    answers = Answer.query.filter_by(
        attempt_id=attempt.id
    ).all()

    return render_template(
        "exam/review_attempt.html",
        attempt=attempt,
        answers=answers
    )

@admin_bp.route("/student-progress")
@login_required
@admin_required
def student_progress():

    stats = (
        db.session.query(
            User.username,
            func.count(ExamAttempt.id).label("attempts"),
            func.avg(ExamAttempt.score).label("avg_score"),
            func.sum(ExamAttempt.passed).label("passes")
        )
        .join(ExamAttempt)
        .group_by(User.id)
        .all()
    )

    return render_template(
        "exam/student_progress.html",
        stats=stats
    )

@admin_bp.route("/students")
@login_required
@admin_required
def list_students():
    page = request.args.get("page", 1, type=int)
    students = User.query.filter_by(role="student").paginate(
        page=page,
        per_page=10
    )
    return render_template("students/students.html", students=students)

@admin_bp.route("/students/<int:user_id>/delete")
@login_required
@admin_required
def delete_student(user_id):
    student = User.query.get_or_404(user_id)
    db.session.delete(student)
    db.session.commit()
    app.logger.info(f"Successfully Removed Student {student.username} Profile.")
    flash("Successfully Removed Student Profile", "success")
    return redirect(url_for('admin_bp.list_students'))

@admin_bp.route("/reset-password/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        temp_pass = secrets.token_urlsafe(8)
        user = User.query.get_or_404(user_id)
        user.password_hash = generate_password_hash(temp_pass)
        user.must_change_password = True
        db.session.commit()
        app.logger.info(f"Password for {user.username} reset successfully.")
        flash("Password reset successfully", "success")
        return jsonify({
            'success': True,
            'username': user.username,
            'password': temp_pass
        }) 
    return jsonify({
        'success': False
    })