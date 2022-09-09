from http import HTTPStatus

from flask_jwt_extended import jwt_required

from api_utils import generate_response_message
from app import create_app

app = create_app()


@app.route("/")
@jwt_required()
def index():
    return generate_response_message(status=HTTPStatus.OK, message="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
