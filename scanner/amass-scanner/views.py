from flask import request, Response
import re
import logging

from app import app


@app.route("/api/amass", methods=["GET", "POST"])
def scan():
    if request.method == "GET":
        return Response(status=405)
        # TODO return the running scans

    elif request.method == "POST":
        data = request.get_json()
        domain = data.get("domain")
        if bool(re.match("[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}", domain)):
            logging.debug(f"Adding {domain} to the amass scan queue")
            app.queue.put(domain)
            return Response(status=201)
        logging.info(f"{data} is not a valid entry")
        return Response(status=400)


@app.route("/api/health", methods=["GET", "POST"])
def health():
    return Response(status=200)