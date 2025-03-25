import requests

def test_get_session_persons():

    # Define the API endpoint [TODO: how to make this work in development and production?]
    base_address = "http://localhost:8080"
    url = base_address + "/api/remote/sessions/get_session_persons"

    # Define the parameters
    params = {
        "instrument_id": "1",  # Replace with the actual instrument_id
        "datetime": "2025-03-06T12:00:00"  # Replace with the actual datetime in ISO 8601 format
    }

    # Make the GET request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Convert the response to JSON
        print(data)
    else:
        print(f"Error: {response.status_code}, {response.text}")

def test_get_remote_allowed():

    # Define the API endpoint [TODO: how to make this work in development and production?]
    base_address = "http://localhost:8080"
    url = base_address + "/api/remote/sessions/get_remote_session_allowed"

    # Define the parameters
    params = {
        "instrument_id": "1",  # Replace with the actual instrument_id
        "datetime": "2025-03-06T12:00:00",  # Replace with the actual datetime in ISO 8601 format
        "username": "mrlarson2"
    }

    # Make the GET request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Convert the response to JSON
        print(data)
    else:
        print(f"Error: {response.status_code}, {response.text}")

if __name__ == '__main__':
    
    # Example #1 for an API query
    test_get_session_persons()

    # Example #2 for an API query
    test_get_remote_allowed()