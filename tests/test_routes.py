import pytest
import json

def test_hello(client):
    response = client.get("/home")
    assert response.json["message"] == "Hello World"

def test_facility(client):
    datas = [{"name": "MCCET"}, {"name": "SCSC"}, {"name": "NCITU"}, {"name": "CCET"}]
    for data in datas:
        resp = client.post("/facility", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        print(json.loads(resp.data))
        assert json.loads(resp.data)["message"] == "new facility created."
    get_resp = client.get("/facility/1")
    assert get_resp.data["name"] == b"MCCET"
    del_resp = client.delete("/facility/4")
    assert del_resp.data["message"] == b"facility CCET got deleted."
    get_list_resp = client.get("/facility")
    assert len(get_list_resp.data) == 3