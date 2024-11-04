import pytest
import json

def test_hello(client):
    response = client.get("/home")
    assert response.json["message"] == "Hello World"

def test_facility(client):
    pass