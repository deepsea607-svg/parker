from flask import redirect, render_template
from flask_jwt_extended import verify_jwt_in_request

from app import app


@app.route("/")
def home():
    try:
        verify_jwt_in_request()
        return redirect("/garage/admin")
    except:
        return render_template("index.html")
