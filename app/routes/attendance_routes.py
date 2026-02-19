from flask import Blueprint, request, jsonify
from app.controllers.attendance_controller import AttendanceController
from app.utils.jwt_required import jwt_required

# Rutas del módulo de Gestión de Asistencias - Proyecto Kallpa UNL
# Incluye endpoints para: registros, horarios, sesiones y estadísticas

attendance_bp = Blueprint("attendance", __name__)
controller = AttendanceController()


def response_handler(result):
    status_code = result.get("code", 200)
    return jsonify(result), status_code

@attendance_bp.route("/attendance/v2/public/participants", methods=["GET"])
@jwt_required
def get_participants():
    # Lista participantes con porcentajes calculados
    program = request.args.get("program")
    result = controller.get_participants(program)
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/schedules", methods=["GET"])
@jwt_required
def get_schedules():
    # Lista horarios/sesiones activas
    result = controller.get_schedules()
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/schedules", methods=["POST"])
@jwt_required
def create_schedule():
    # Creación con validaciones de solapamiento
    data = request.json
    result = controller.create_schedule(data)
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/schedules/<schedule_id>", methods=["PUT"])
@jwt_required
def update_schedule(schedule_id):
    # Modificación de horarios existentes
    data = request.json
    result = controller.update_schedule(schedule_id, data)
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/schedules/<schedule_id>", methods=["DELETE"])
@jwt_required
def delete_schedule(schedule_id):
    # Eliminación lógica (marca como inactivo)
    result = controller.delete_schedule(schedule_id)
    return response_handler(result)

@attendance_bp.route("/attendance/v2/public/history", methods=["GET"])
@jwt_required
def get_history():
    # Historial con filtros de rango de fechas, sesión y búsqueda por participante
    date_from = request.args.get("date_from") or request.args.get("startDate")
    date_to = request.args.get("date_to") or request.args.get("endDate")
    schedule_id = request.args.get("schedule_id") or request.args.get("scheduleId")
    day_filter = request.args.get("day_of_week")
    # Nuevos filtros de búsqueda por participante
    search_dni = request.args.get("dni")
    search_name = request.args.get("name") or request.args.get("search")
    participant_id = request.args.get("participant_id") or request.args.get("participantId")
    
    result = controller.get_history(date_from, date_to, schedule_id, day_filter, search_dni, search_name, participant_id)
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/history/session/<schedule_id>/<date>", methods=["GET"])
@jwt_required
def get_session_detail(schedule_id, date):
    # Detalle completo de participantes en una sesión específica
    result = controller.get_session_detail(schedule_id, date)
    return response_handler(result)


@attendance_bp.route("/attendance/v2/public/history/session/<schedule_id>/<date>", methods=["DELETE"])
@jwt_required
def delete_session_attendance(schedule_id, date):
    # Eliminar todos los registros de una fecha
    result = controller.delete_session_attendance(schedule_id, date)
    return response_handler(result)


@attendance_bp.route("/attendance/session/<schedule_id>/<date>", methods=["DELETE"])
@jwt_required
def delete_session_attendance_legacy(schedule_id, date):
    # Eliminación de sesión sin prefijo v2
    result = controller.delete_session_attendance(schedule_id, date)
    return response_handler(result)

@attendance_bp.route("/attendance/v2/public/register", methods=["POST"])
@jwt_required
def register_public_attendance():
    # Endpoint principal para registro desde dashboard
    data = request.json
    result = controller.register_public_attendance(data)
    return response_handler(result)