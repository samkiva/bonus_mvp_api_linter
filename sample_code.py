from flask import Flask, request

app = Flask(__name__)

@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Gets a user's details."""
    # ... logic ...
    return {"user_id": user_id, "name": "Test User"}

@app.route("/user", methods=["POST"])
def create_user(username, email, password): # <-- Problem here!
    """Creates a new user."""
    # This function's parameters are in the signature,
    # not from request.form. This is a simple example
    # for the AST parser to find.
    # A real app might use request.json, but this
    # clearly demonstrates the parameter mismatch.
    return {"status": "created", "username": username}, 201

@app.route("/health", methods=["GET"])
def health_check():
    """A simple health check."""
    return {"status": "ok"}

def not_an_api_route():
    """This function should be ignored by the linter."""
    pass
