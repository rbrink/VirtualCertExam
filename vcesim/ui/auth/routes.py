import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, \
    request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from vcesim.models.user import User
from vcesim.ui import db
from vcesim.ui.forms import LoginForm, RegisterStudent
from vcesim.ui.utils import admin_required

auth_bp = Blueprint("auth_bp", __name__,
                    template_folder="templates",
                    static_folder="../static")

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # If already authenticated, redirect to the appropriate dashboard
    if current_user.is_authenticated:
        if getattr(current_user, 'role', None) == "admin":
            return redirect(url_for("admin_bp.dashboard"))
        return redirect(url_for("student_bp.dashboard"))

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            print("DEBUG: Logged in user role:", user.role)
            if user.must_change_password:
                print("DEBUG: Redirecting student to change password")
                return redirect(url_for('auth_bp.change_password'))            
            flash("Login successful", "success")
            # Use url_for with the blueprint endpoints
            if getattr(user, 'role', None) == "admin":
                return redirect(url_for("admin_bp.dashboard"))
            print("DEBUG: Redirecting student to dashboard")
            return redirect(url_for("student_bp.dashboard"))
        else:
            flash("Invalid Username/Password", "error")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout successful", "success")
    return redirect(url_for("auth_bp.login"))

@auth_bp.route("/register", methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegisterStudent()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        if form.validate():
            temp_pass = secrets.token_urlsafe(8)
            new_user = User(
                username=form.username.data.strip(),
                password_hash=generate_password_hash(temp_pass),
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                course=form.course.data,
                instructor=form.instructor.data,
                role=form.role.data,
                must_change_password=True
                )
            db.session.add(new_user)
            db.session.commit()
            return jsonify({
                "success": True,
                "username": new_user.username,
                "password": temp_pass
                })
        return jsonify({
            "success": False,
            "errors": form.errors
            })
    return render_template("register_student.html", form=form)

@auth_bp.route("/change-password", methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form["password"]
        current_user.password_hash = generate_password_hash(new_password)
        current_user.must_change_password = False
        db.session.commit()
        flash("Password changed successfully", "success")
        if current_user.role == "admin":
            return redirect(url_for('admin_bp.dashboard'))
        else:
            return redirect(url_for('student_bp.dashboard'))
    return render_template("change_password.html")