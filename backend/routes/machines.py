from flask import Blueprint, jsonify, request

machines_bp = Blueprint("machines", __name__)

@machines_bp.route("/", methods=["GET", "POST"])
def get_machines():
    if request.method == "POST":
        return jsonify({"machines": ["mac1", "mac2", "mac3"]})
    if request.method == "GET":

        return jsonify({"machines": ["mac1", "mac2", "mac3"]})