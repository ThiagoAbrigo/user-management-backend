from flask import Blueprint, request, jsonify
from app.controllers.assessment_controller import AssessmentController
from app.models.activityLog import ActivityLog
from app.utils.jwt_required import jwt_required

assessment_bp = Blueprint("assessment", __name__)
controller = AssessmentController()


def response_handler(result):
    status_code = result.get("code", 200)
    return jsonify(result), status_code


@assessment_bp.route("/save-assessment", methods=["POST"])
@jwt_required
def register_evaluation():
    data = request.json
    return response_handler(controller.register(data))


@assessment_bp.route("/list-assessment", methods=["GET"])
@jwt_required
def list_evaluation():
    return response_handler(controller.get_assessment())


@assessment_bp.route("/update-assessment/<string:external_id>", methods=["PUT"])
@jwt_required
def update_evaluation(external_id):
    data = request.json
    return response_handler(controller.update(external_id, data))


@assessment_bp.route(
    "/participants/<string:participant_external_id>/assessments", methods=["GET"]
)
@jwt_required
def search_evaluation(participant_external_id):
    return response_handler(
        controller.get_participants_external_id(participant_external_id)
    )
