from flask import render_template, redirect, url_for
from vcesim.ui import app

@app.route("/")
def home():
    return redirect(url_for("auth_bp.login"))