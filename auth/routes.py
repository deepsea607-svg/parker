from flask import request , jsonify , render_template , redirect
from flask_jwt_extended import create_access_token , set_access_cookies , unset_access_cookies , jwt_required , verify_jwt_in_request
from auth import auth
from app.models import db , User


# register api routes

from sqlalchemy.exc import IntegrityError


@auth.route("/reg-api", methods=["POST"])
def reg_api():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Invalid or missing JSON body"}), 400

    # required fields
    required = ["username", "password", "password2", "contact", "address"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"msg": f"Missing fields: {', '.join(missing)}"}), 400

    username = data["username"].strip()
    password = data["password"].strip()
    password2 = data["password2"].strip()
    contact = data["contact"].strip()
    address = data["address"].strip()


    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already taken"}), 409

    new_user = User(username=username,password=password,contact=contact,address=address) #type:ignore

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Username already taken"}), 409

    return jsonify({
        "msg": "User registered successfully",
    }), 201
    
        
# register api routes
@auth.route("/login-api",methods=["POST"])
def login_api():
    
    data = request.get_json()
    username = data.get("username").strip()
    password = data.get("password").strip()

    user = User.query.filter_by(username=username).first()

    if not user or password != user.password:
        return jsonify({"msg": "Invalid username or password"}), 401

    # Generate JWT token
    access_token = create_access_token(identity=str(user.id))
    resp = jsonify({"msg": "login successful"},200)
    set_access_cookies(resp,access_token)
    return resp


@auth.route("/logout-api", methods=["POST"])
@jwt_required()
def logout_api():
    resp = jsonify({"msg": "logged out"})
    unset_access_cookies(resp)
    return resp, 200



#page serving routes
@auth.route("/register")
def register():
    try:
        verify_jwt_in_request()
        return redirect("/garage/admin")
    except:
        return render_template('register.html')

@auth.route("/login")
def login():
    try:
        verify_jwt_in_request()
        return redirect("/garage/admin")
    except:
        return render_template('login.html')