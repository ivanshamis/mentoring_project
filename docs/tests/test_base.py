from http import HTTPStatus


def test_unauthorized(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_authorized(client, auth_headers):
    response = client.get('/', headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.json["result"] == "ok"
