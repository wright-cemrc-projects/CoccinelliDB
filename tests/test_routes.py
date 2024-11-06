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
        assert json.loads(resp.data)["message"] == "new facility created."
    get_resp = client.get("/facility/1")
    assert json.loads(get_resp.data)["name"] == "MCCET"
    del_resp = client.delete("/facility/4")
    assert json.loads(del_resp.data)["message"] == "<Facility(name=CCET)> got deleted."
    get_list_resp = client.get("/facility")
    assert len(json.loads(get_list_resp.data)) == 3

def test_group(client):
    client.post("/facility", data=json.dumps({"name": "MCCET"}), headers={"Content-Type": "application/json"})
    facility_resp = client.get("/facility")
    assert len(json.loads(facility_resp.data)) == 1
    datas = [{"name": "matt_group", "facility_id": 1}, {"name": "liz_group", "facility_id": 1}]
    for data in datas:
        resp = client.post("/group", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["message"] == f"new group {data['name']} created."
    get_resp = client.get("/group/1")
    assert json.loads(get_resp.data)["name"] == "matt_group"
    del_resp = client.delete("/group/2")
    assert json.loads(del_resp.data)["message"] == "<FacilityGroup(name=liz_group)> got deleted."
    update_resp = client.post("/group/1", data=json.dumps({"name": "Matt_group"}), headers={"Content-Type": "application/json"})
    update_get_resp = client.get("/group/1")
    assert json.loads(update_get_resp.data)["name"] == "Matt_group"

def test_person(client):
    pass
