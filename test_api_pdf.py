# tests/smoke_flight_ticket.py
import os
from io import BytesIO
from fastapi.testclient import TestClient

# change this import to your app location, e.g. from src.main import app
from app import app

client = TestClient(app)

SAMPLES_DIR = "/Users/akhilbabu/Documents/work/servers/lyik_services/test/samples"
FILES = [
    os.path.join(SAMPLES_DIR, f)
    for f in os.listdir(SAMPLES_DIR)
    # if os.path.isfile(os.path.join(SAMPLES_DIR, f)) and f.lower().endswith(".pdf")
]


def post_one(file_tuple):
    resp = client.post(
        "/process",
        data={
            "service_name": "known_ocr",
            "license_key": os.getenv("LICENSE_KEY", "dummy"),
            "license_endpoint": os.getenv("LICENSE_EP", ""),
            "document_type": "flight_ticket",
        },
        files=[("files", file_tuple)],
    )
    # just print whatever the API returns; no validation/assertions
    print("STATUS:", resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


def main():
    if not FILES:
        # fallback tiny in-memory PDF so the script always runs
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        post_one(("ticket.pdf", BytesIO(pdf_bytes), "application/pdf"))
    else:
        for path in FILES:
            with open(path, "rb") as f:
                post_one((os.path.basename(path), f, "application/pdf"))


if __name__ == "__main__":
    main()
