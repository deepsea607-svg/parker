from app import app
from garage import garage #type:ignore
from auth import auth

app.register_blueprint(garage)
app.register_blueprint(auth)

if __name__ == "__main__":
    app.run()