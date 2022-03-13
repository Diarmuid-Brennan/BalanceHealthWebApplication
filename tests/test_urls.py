from flask import request, session


def test_up(client):
    assert client.get("/login").status_code == 200
    response = client.get("/login")

    assert response.data.startswith(b"<!DOCTYPE html>") == True
    assert b'<form method="POST"' in response.data
    data = {"email": "bob@email.com", "password": "bob123"}
    r = client.post("/login", json=data)
    assert r.status_code == 200


def test_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert response.data.startswith(b"<!DOCTYPE html>") == True
