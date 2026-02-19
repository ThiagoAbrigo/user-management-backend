from flask import Blueprint, request, jsonify
from sqlalchemy.sql.visitors import ExternallyTraversible
from app.controllers.evaluation_controller import EvaluationController
from app.utils.roles_required import roles_required
from app.utils.jwt_required import jwt_required

evaluation_bp = Blueprint("evaluation", __name__)
controller = EvaluationController()


def response_handler(result):
    status_code = result.get("code", 200)
    return jsonify(result), status_code


@evaluation_bp.route("/list-test", methods=["GET"])
@jwt_required
def list_test():
    return response_handler(controller.list())


@evaluation_bp.route("/save-test", methods=["POST"])
# @roles_required("DOCENTE")
@jwt_required
def register_evaluation():
    data = request.json
    return response_handler(controller.register(data))


@evaluation_bp.route("/apply_test", methods=["POST"])
# @roles_required("DOCENTE", "PASANTE")
@jwt_required
def apply_test():
    data = request.json
    return response_handler(controller.apply_test(data))

@evaluation_bp.route("/participant-progress", methods=["GET"])
@jwt_required
def participant_progress():
    participant_external_id = request.args.get("participant_external_id")
    return response_handler(
        controller.get_participant_progress(participant_external_id)
    )

@evaluation_bp.route("/list-tests-participant", methods=["GET"])
@jwt_required
def list_tests_for_participant_endpoint():
    participant_external_id = request.args.get("participant_external_id")
    return response_handler(
        controller.list_tests_for_participant(participant_external_id)
    )


@evaluation_bp.route("/get-test/<external_id>", methods=["GET"])
@jwt_required
def get_test_detail(external_id):
    return response_handler(controller.get_by_external_id(external_id))


@evaluation_bp.route("/update-test", methods=["PUT"])
@jwt_required
def update_test():
    data = request.json
    return response_handler(controller.update(data))


@evaluation_bp.route("/delete-test/<external_id>", methods=["DELETE"])
@jwt_required
def delete_test(external_id):
    return response_handler(controller.delete(external_id))
