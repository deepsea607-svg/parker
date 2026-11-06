from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Garage(db.Model):
    __tablename__ = "garages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=False)

    time_slot = db.Column(db.String(50), nullable=False)
    day_slot = db.Column(db.String(50), nullable=False)

    two_wheeler_capacity = db.Column(db.Integer, nullable=False, default=0)
    four_wheeler_capacity = db.Column(db.Integer, nullable=False, default=0)

    slots = db.relationship("Slot", backref="garage", lazy=True, cascade="all, delete-orphan")


class Slot(db.Model):
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)

    slot_no = db.Column(db.String(20), nullable=False)
    vehicle_type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")

    booked_by = db.Column(db.String(100), nullable=True)
    contact = db.Column(db.String(15), nullable=True)

    __table_args__ = (db.UniqueConstraint("garage_id", "slot_no", name="uq_garage_slot_no"),)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    garages = db.relationship("Garage", backref="owner", lazy=True, cascade="all, delete-orphan")
