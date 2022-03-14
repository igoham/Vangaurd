from flask import request, Response
from app import app
import logging


def validate_amass_scan_data(data) -> bool:
    if data.get("name") is None:
        return False
    if data.get('domain') is None:
        return False
    if data.get("addresses") is None:
        return False
    if data.get("type") is None:
        return False
    return True


@app.route("/api/scan", methods=["GET", "POST"])
def scan():
    if request.method == "GET":
        return Response(status=405)
        # TODO return the running scans
    # TODO no longer posting to api directly can be removed
    elif request.method == "POST":
        data = request.get_json()
        if validate_amass_scan_data(data) is True:
            logging.info(f"Adding {data.get('name')} with {len(data.get('addresses'))} addresses. \nIPs:{[d.get('ip') for d in data.get('addresses')]}")
            app.queue.put(data)
            # Return created response
            return Response(status=201)
        # Return error response
        return Response(status=400)


@app.route("/api/health", methods=["GET", "POST"])
def health():
    return Response(status=200)