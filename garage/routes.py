import json

from flask import abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Garage, Slot, User, db
from garage import garage


# admin route : handles html and date via jinja
@garage.route("/admin")
@jwt_required()
def admin():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=int(user_id)).first()

    if not user:
        return "User not found", 404

    user_data = {
        "id": user.id,
        "username": user.username,
        "contact": user.contact,
        "address": user.address,
        "garages": [
            {
                "id": garage.id,
                "name": garage.name,
                "address": garage.address,
                "contact": garage.contact,
                "time_slot": garage.time_slot,
                "day_slot": garage.day_slot,
                "two_wheeler_capacity": garage.two_wheeler_capacity,
                "four_wheeler_capacity": garage.four_wheeler_capacity,
                "slots": [
                    {
                        "id": slot.id,
                        "slot_no": slot.slot_no,
                        "vehicle_type": slot.vehicle_type,
                        "status": slot.status,
                        "booked_by": slot.booked_by,
                        "contact": slot.contact,
                    }
                    for slot in garage.slots
                ],
            }
            for garage in user.garages
        ],
    }

    return render_template("admin.html", user_data=user_data)


# A post api endpint for posting all admin registrations
@garage.route("/api", methods=["POST"])
@jwt_required()
def add_garage():
    data = request.form if request.form else request.json
    action = data.get("action")

    try:
        if action == "delete":
            garage_name = data.get("garage_name")
            garage_to_delete = Garage.query.filter_by(name=garage_name).first()

            if garage_to_delete:
                db.session.delete(garage_to_delete)
                db.session.commit()

            if request.form:
                return redirect("/garage/admin")
            return jsonify({"message": "Garage deleted successfully!"}), 200

        user_id = data.get("user_id")
        name = data.get("name")
        address = data.get("address")
        contact = data.get("contact")
        time_slot = data.get("time_slot")
        day_slot = data.get("day_slot")
        two_wheeler_capacity = int(data.get("two_wheeler_capacity", 0))
        four_wheeler_capacity = int(data.get("four_wheeler_capacity", 0))

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found!"}), 404

        existing_garage = Garage.query.filter_by(user_id=user_id, name=name).first()

        if existing_garage:
            existing_garage.address = address  # type: ignore
            existing_garage.contact = contact  # type: ignore
            existing_garage.time_slot = time_slot  # type: ignore
            existing_garage.day_slot = day_slot  # type: ignore

            current_two_slots = [s for s in existing_garage.slots if s.vehicle_type == "2W"]
            diff_two = two_wheeler_capacity - len(current_two_slots)

            if diff_two > 0:
                start_idx = len(current_two_slots) + 1
                for i in range(start_idx, two_wheeler_capacity + 1):
                    db.session.add(
                        Slot(garage_id=existing_garage.id, slot_no=f"2W-{i}", vehicle_type="2W", status="available")
                    )
            elif diff_two < 0:
                unbooked_two = [s for s in current_two_slots if s.status == "available"]
                unbooked_two.sort(key=lambda s: int(s.slot_no.split("-")[1]), reverse=True)

                to_remove_count = abs(diff_two)
                for s in unbooked_two:
                    if to_remove_count > 0:
                        db.session.delete(s)
                        to_remove_count -= 1

            current_four_slots = [s for s in existing_garage.slots if s.vehicle_type == "4W"]
            diff_four = four_wheeler_capacity - len(current_four_slots)

            if diff_four > 0:
                start_idx = len(current_four_slots) + 1
                for i in range(start_idx, four_wheeler_capacity + 1):
                    db.session.add(
                        Slot(garage_id=existing_garage.id, slot_no=f"4W-{i}", vehicle_type="4W", status="available")
                    )
            elif diff_four < 0:
                unbooked_four = [s for s in current_four_slots if s.status == "available"]
                unbooked_four.sort(key=lambda s: int(s.slot_no.split("-")[1]), reverse=True)

                to_remove_count = abs(diff_four)
                for s in unbooked_four:
                    if to_remove_count > 0:
                        db.session.delete(s)
                        to_remove_count -= 1

            existing_garage.two_wheeler_capacity = two_wheeler_capacity
            existing_garage.four_wheeler_capacity = four_wheeler_capacity
        else:
            new_garage = Garage(
                user_id=user_id,  # type:ignore
                name=name,  # type:ignore
                address=address,  # type:ignore
                contact=contact,  # type:ignore
                time_slot=time_slot,  # type:ignore
                day_slot=day_slot,  # type:ignore
                two_wheeler_capacity=two_wheeler_capacity,  # type:ignore
                four_wheeler_capacity=four_wheeler_capacity,  # type:ignore
            )

            db.session.add(new_garage)
            db.session.flush()
            for i in range(1, two_wheeler_capacity + 1):
                slot = Slot(
                    garage_id=new_garage.id,
                    slot_no=f"2W-{i}",
                    vehicle_type="2W",
                    status="available",
                    booked_by=None,
                    contact=None,
                )
                db.session.add(slot)

            for i in range(1, four_wheeler_capacity + 1):
                slot = Slot(
                    garage_id=new_garage.id,
                    slot_no=f"4W-{i}",
                    vehicle_type="4W",
                    status="available",
                    booked_by=None,
                    contact=None,
                )
                db.session.add(slot)

            message = "Garage and slots populated successfully!"

        db.session.commit()

        if request.form:
            return redirect("/garage/admin")

        return jsonify({"message": message}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# for all qr routes : the form submission and cookies obtaining is handled by this route
@garage.route("/qr/<string:username>/<int:garage_id>", methods=["GET", "POST"])
def slot_booking_qr(username, garage_id):
    print(username, garage_id)
    user = User.query.filter_by(username=username).first_or_404()
    garage = Garage.query.filter_by(id=garage_id, user_id=user.id).first_or_404()
    print(user, garage)

    cookie_name = f"parking_slot_{garage_id}"

    if request.method == "GET":
        booked_cookie = request.cookies.get(cookie_name)
        if booked_cookie:
            try:
                cookie_data = json.loads(booked_cookie)
                slot = Slot.query.filter_by(id=cookie_data.get("slot_id"), garage_id=garage.id).first()

                expected = f"{cookie_data.get('name')} ({cookie_data.get('vehicle_no')})"
                if slot and slot.booked_by == expected:
                    slot.status = "available"
                    slot.booked_by = None
                    slot.contact = None
                    db.session.commit()
            except ValueError, TypeError:
                pass  # malformed cookie

            resp = make_response(redirect(url_for("garage.slot_booking_qr", username=username, garage_id=garage_id)))
            resp.delete_cookie(cookie_name)
            return resp

        return render_template("booking.html", username=username, garage=garage)

    name = request.form.get("name")
    vehicle_type_input = request.form.get("vehicle_type")  # "two" or "four"
    vehicle_no = request.form.get("vehicle_no")
    contact = request.form.get("contact")

    v_type_db = "2W" if vehicle_type_input == "two" else "4W"

    available_slot = (
        Slot.query.filter_by(garage_id=garage.id, vehicle_type=v_type_db, status="available").with_for_update().first()
    )
    if not available_slot:
        return "Sorry, no available slots left for this vehicle type.", 400

    available_slot.status = "booked"
    available_slot.booked_by = f"{name} ({vehicle_no})"
    available_slot.contact = contact
    db.session.commit()

    slot_cookie_payload = {
        "slot_id": available_slot.id,
        "slot_no": available_slot.slot_no,
        "name": name,
        "vehicle_no": vehicle_no,
    }

    resp = make_response(
        render_template(
            "booking_success.html",
            garage=garage,
            slot_no=available_slot.slot_no,
            name=name,
            vehicle_no=vehicle_no,
        )
    )
    resp.set_cookie(
        cookie_name,
        json.dumps(slot_cookie_payload),
        max_age=60 * 60 * 24,
        httponly=True,
        samesite="Lax",
    )
    return resp


# for public facing table : html served by this endpoint
@garage.route("/<string:username>/<int:garage_id>")
def public_garage_timetable(username, garage_id):
    user = User.query.filter_by(username=username).first_or_404()

    user_data = {
        "id": user.id,
        "username": user.username,
        "contact": user.contact,
        "address": user.address,
        "garages": [
            {
                "id": g.id,
                "name": g.name,
                "address": g.address,
                "contact": g.contact,
                "time_slot": g.time_slot,
                "day_slot": g.day_slot,
                "two_wheeler_capacity": g.two_wheeler_capacity,
                "four_wheeler_capacity": g.four_wheeler_capacity,
                "slots": [
                    {
                        "id": s.id,
                        "slot_no": s.slot_no,
                        "vehicle_type": s.vehicle_type,
                        "status": s.status,
                        "booked_by": s.booked_by,
                        "contact": s.contact,
                    }
                    for s in g.slots
                ],
            }
            for g in user.garages
        ],
    }

    current_garage = next((g for g in user_data["garages"] if g["id"] == garage_id), None)

    if not current_garage:
        abort(404)

    return render_template("public.html", garage=current_garage, user_data=user_data)

