import requests


def test_pincode_service(pin: int):
    """"""
    data = {
        "service_name": "pin_code_data_extraction",
        "pin_code": {pin},
    }

    response = requests.post(f"http://localhost:8000/process", data=data)
    print(response.json())


test_pincode_service(pin=799004)
