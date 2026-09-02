import pytest
import json

def test_hello(client):
    response = client.get("/api/home")
    assert response.json["message"] == "Hello World"

def test_facility(client):
    datas = [{"name": "MCCET"}, {"name": "SCSC"}, {"name": "NCITU"}, {"name": "CCET"}]
    for data in datas:
        resp = client.post("/api/facilities", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["message"] == "new facility created."
    get_resp = client.get("/api/facilities/1")
    assert json.loads(get_resp.data)["name"] == "MCCET"
    del_resp = client.delete("/api/facilities/4")
    assert json.loads(del_resp.data)["message"] == "<Facility(name=CCET)> got deleted."
    get_list_resp = client.get("/api/facilities")
    assert len(json.loads(get_list_resp.data)) == 3

def test_group(client):
    client.post("/api/facilities", data=json.dumps({"name": "MCCET"}), headers={"Content-Type": "application/json"})
    facility_resp = client.get("/api/facilities")
    assert len(json.loads(facility_resp.data)) == 1
    datas = [{"name": "matt_group"}, {"name": "liz_group"}]
    for data in datas:
        resp = client.post("/api/groups", data=json.dumps(data), headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["message"] == f"new group {data['name']} created."
    get_resp = client.get("/api/groups/1")
    assert json.loads(get_resp.data)["name"] == "matt_group"
    del_resp = client.delete("/api/groups/2")
    assert json.loads(del_resp.data)["message"] == "<Group(name=liz_group)> got deleted."
    update_resp = client.patch("/api/groups/1", data=json.dumps({"name": "Matt_group"}), headers={"Content-Type": "application/json"})
    update_get_resp = client.get("/api/groups/1")
    assert json.loads(update_get_resp.data)["name"] == "Matt_group"

def test_person(client):
    client.post("/api/facilities", data=json.dumps({"name": "MCCET"}), headers={"Content-Type": "application/json"})
    client.post("/api/groups", data=json.dumps({"name": "matt_group"}), headers={"Content-Type": "application/json"})
    create_person_resp = client.post("/api/persons", data=json.dumps({"first_name": "Yan", "last_name": "Zhuang", "email": "yzhuang63@wisc.edu", "net_id": "9084938471"}), headers={"Content-Type": "application/json"})
    assert create_person_resp.status_code == 200
    assert json.loads(create_person_resp.data)["message"] == "Person(name=Yan Zhuang, email=yzhuang63@wisc.edu) created."

    # The seeded test-admin user (see conftest.py) already occupies id 1, so
    # look this person up by email rather than assuming an id.
    person_list = json.loads(client.get("/api/persons").data)
    person_id = next(p["id"] for p in person_list if p["email"] == "yzhuang63@wisc.edu")

    get_person_resp = client.get(f"/api/persons/{person_id}")
    assert json.loads(get_person_resp.data)["email"] == "yzhuang63@wisc.edu"
    update_person_resp = client.patch(f"/api/persons/{person_id}", data=json.dumps({"organization": "UW Madison"}), headers={"Content-Type": "application/json"})
    assert update_person_resp.status_code == 200
    assert json.loads(update_person_resp.data)["message"] == "Person(name=Yan Zhuang, email=yzhuang63@wisc.edu) got updated."
    update_get_person_resp = client.get(f"/api/persons/{person_id}")
    assert json.loads(update_get_person_resp.data)["organization"] == "UW Madison"
    delete_person_resp = client.delete(f"/api/persons/{person_id}")
    assert json.loads(delete_person_resp.data)["message"] == "Person(name=Yan Zhuang, email=yzhuang63@wisc.edu) got deleted."
