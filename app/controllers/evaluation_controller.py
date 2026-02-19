from app.models.evaluation import Evaluation
from app.models.evaluationResult import EvaluationResult
from app.models.participant import Participant
from app.models.test import Test
from app.models.testExercise import TestExercise
from app.utils.constants.message import (
    ERROR_EX_DUPLICATED,
    ERROR_EX_NOT_IN_TEST,
    ERROR_INTERNAL,
    ERROR_PARTICIPANT_NOT_FOUND,
    ERROR_TEST_NOT_FOUND,
    ERROR_VALIDATION,
    ERROR_VALUE_INVALID,
    INVALID_DATA,
    REQUIRED_FIELD,
    SUCCESS_APPLY_TEST,
    TEST_CREATED,
    TEST_EDIT_FORBIDDEN,
    TEST_NOT_FOUND,
    TEST_UPDATED,
)
from app.utils.responses import error_response, success_response
from app import db
from datetime import datetime

from app.utils.validations.evaluation_validation import (
    parse_evaluation_date,
    validate_apply_test_input,
    validate_exercises,
    validate_register_input,
    validate_test_fields,
    validate_update_input,
)


def has_evaluation_results(test_id):
    return (
        db.session.query(EvaluationResult.id)
        .join(TestExercise, EvaluationResult.test_exercise_id == TestExercise.id)
        .filter(TestExercise.test_id == test_id)
        .first()
        is not None
    )


def replace_test_exercises(test_id, exercises):
    TestExercise.query.filter_by(test_id=test_id).delete(synchronize_session=False)

    created = []
    for ex in exercises:
        exercise = TestExercise(
            test_id=test_id,
            name=ex["name"].strip(),
            unit=ex["unit"].strip(),
        )
        db.session.add(exercise)
        created.append(
            {
                "name": exercise.name,
                "unit": exercise.unit,
            }
        )
    return created


def get_valid_test_exercises(test_id):
    return {
        ex.external_id: ex.id
        for ex in TestExercise.query.filter_by(test_id=test_id).all()
    }


def validate_and_create_results(evaluation_id, results, valid_exercises):
    used = set()

    for r in results:
        ex_id = valid_exercises.get(r.get("test_exercise_external_id"))

        if not ex_id:
            return ERROR_EX_NOT_IN_TEST

        if ex_id in used:
            return ERROR_EX_DUPLICATED

        used.add(ex_id)

        value = r.get("value") or 0
        if not isinstance(value, (int, float)) or value < 0:
            return ERROR_VALUE_INVALID

        db.session.add(
            EvaluationResult(
                evaluation_id=evaluation_id,
                test_exercise_id=ex_id,
                value=value,
            )
        )

    return None


class EvaluationController:

    def list(self):
        try:
            tests = Test.query.all()

            result = []
            for test in tests:
                exercises = TestExercise.query.filter_by(test_id=test.id).all()
                exercises_data = [
                    {"external_id": ex.external_id, "name": ex.name, "unit": ex.unit}
                    for ex in exercises
                ]

                result.append(
                    {
                        "external_id": test.external_id,
                        "name": test.name,
                        "description": test.description,
                        "frequency_months": test.frequency_months,
                        "exercises": exercises_data,
                        "status": test.status,
                        "already_done": bool(
                            db.session.query(EvaluationResult.id)
                            .join(
                                TestExercise,
                                EvaluationResult.test_exercise_id == TestExercise.id,
                            )
                            .filter(TestExercise.test_id == test.id)
                            .first()
                        ),
                    }
                )

            return success_response(msg="Listado de tests con ejercicios", data=result)

        except Exception as e:
            return error_response(f"Internal error: {str(e)}", 500)

    def register(self, data):
        try:
            errors = {}

            errors.update(validate_register_input(data))
            if errors:
                return error_response(INVALID_DATA, code=400)

            name = data.get("name", "").strip()
            frequency = data.get("frequency_months")
            description = (
                data.get("description", "").strip() if data.get("description") else None
            )
            exercises = data.get("exercises", [])

            errors.update(validate_test_fields(name, frequency))
            errors.update(validate_exercises(exercises))

            if errors:
                return error_response(
                    msg=ERROR_VALIDATION, data={"validation_errors": errors}, code=400
                )

            test = Test(
                name=name.lower(),
                description=description,
                frequency_months=frequency,
            )

            db.session.add(test)
            db.session.flush()

            exercises_created = []
            for ex in exercises:
                exercise = TestExercise(
                    test_id=test.id,
                    name=ex["name"].strip(),
                    unit=ex["unit"].strip(),
                )
                db.session.add(exercise)
                exercises_created.append(
                    {
                        "name": exercise.name,
                        "unit": exercise.unit,
                    }
                )

            db.session.commit()

            return success_response(
                msg=TEST_CREATED,
                data={
                    "test_external_id": test.external_id,
                    "name": test.name,
                    "frequency_months": test.frequency_months,
                    "description": test.description,
                    "exercises": exercises_created,
                },
                code=200,
            )

        except Exception:
            db.session.rollback()
            return error_response(ERROR_INTERNAL, code=500)

    def update(self, data):
        try:
            if not isinstance(data, dict):
                return error_response(INVALID_DATA, code=400)

            test_external_id = data.get("external_id")
            if not test_external_id:
                return error_response(
                    msg=ERROR_VALIDATION,
                    data={"test_external_id": REQUIRED_FIELD},
                    code=400,
                )

            test = Test.query.filter_by(external_id=test_external_id).first()
            if not test:
                return error_response(
                    msg=ERROR_VALIDATION,
                    data={"test_external_id": TEST_NOT_FOUND},
                    code=400,
                )

            if has_evaluation_results(test.id):
                return error_response(
                    msg=TEST_EDIT_FORBIDDEN,
                    data={
                        "test_external_id": "Este test ya ha sido aplicado a participantes"
                    },
                    code=400,
                )

            errors = validate_update_input(data, test)
            if errors:
                return error_response(
                    msg=ERROR_VALIDATION,
                    data=errors,
                    code=400,
                )

            test.name = data["name"].strip().lower()
            test.frequency_months = data["frequency_months"]
            test.description = (
                data.get("description", "").strip() if data.get("description") else None
            )

            exercises_updated = replace_test_exercises(
                test.id, data.get("exercises", [])
            )

            db.session.commit()

            return success_response(
                msg=TEST_UPDATED,
                data={
                    "external_id": test.external_id,
                    "name": test.name,
                    "frequency_months": test.frequency_months,
                    "description": test.description,
                    "exercises": exercises_updated,
                },
                code=200,
            )

        except Exception:
            db.session.rollback()
            return error_response(ERROR_INTERNAL, code=500)

    def apply_test(self, data):
        try:
            error = validate_apply_test_input(data)
            if error:
                return error_response(error)

            participant = Participant.query.filter_by(
                external_id=data["participant_external_id"]
            ).first()
            if not participant:
                return error_response(ERROR_PARTICIPANT_NOT_FOUND)

            test = Test.query.filter_by(external_id=data["test_external_id"]).first()
            if not test:
                return error_response(ERROR_TEST_NOT_FOUND)

            if error:
                return error_response(error)

            evaluation = Evaluation(
                participant_id=participant.id,
                test_id=test.id,
                general_observations=data.get("general_observations"),
            )

            db.session.add(evaluation)
            db.session.flush()

            valid_exercises = get_valid_test_exercises(test.id)

            error = validate_and_create_results(
                evaluation.id,
                data.get("results", []),
                valid_exercises,
            )
            if error:
                return error_response(error)

            db.session.commit()

            return success_response(
                msg=SUCCESS_APPLY_TEST,
                data={"evaluation_external_id": evaluation.external_id},
            )

        except Exception:
            db.session.rollback()
            return error_response(ERROR_INTERNAL, code=500)

    def get_participant_progress(self, participant_external_id):
        try:
            participant = Participant.query.filter_by(
                external_id=participant_external_id
            ).first()

            if not participant:
                return error_response("Participante no encontrado")

            evaluations = (
                Evaluation.query.filter_by(participant_id=participant.id)
                .order_by(Evaluation.date.asc())
                .all()
            )

            progress_data = []

            for eval in evaluations:
                results = EvaluationResult.query.filter_by(evaluation_id=eval.id).all()

                result_dict = {r.exercise.name: r.value for r in results}

                total = sum(result_dict.values()) if result_dict else 0

                progress_data.append(
                    {
                        "evaluation_external_id": eval.external_id,
                        "date": eval.date.strftime("%Y-%m-%d") if eval.date else None,
                        "test_name": eval.test.name,  # 👈 AQUÍ
                        "results": result_dict,
                        "total": total,
                        "general_observations": eval.general_observations,
                    }
                )

            return success_response(
                msg="Progreso obtenido correctamente",
                data={
                    "participant_name": participant.firstName,
                    "progress": progress_data,
                },
            )

        except Exception as e:
            return error_response(f"Internal error: {str(e)}", 500)

    def list_tests_for_participant(self, participant_external_id):
        try:
            participant = Participant.query.filter_by(
                external_id=participant_external_id
            ).first()
            if not participant:
                return error_response("Participante no encontrado", 404)

            tests = Test.query.filter_by(status="Activo").all()

            result = []
            for test in tests:
                exercises = TestExercise.query.filter_by(test_id=test.id).all()
                exercises_data = [
                    {"external_id": ex.external_id, "name": ex.name, "unit": ex.unit}
                    for ex in exercises
                ]

                evaluation = Evaluation.query.filter_by(
                    participant_id=participant.id, test_id=test.id
                ).first()

                result.append(
                    {
                        "external_id": test.external_id,
                        "name": test.name,
                        "description": test.description,
                        "frequency_months": test.frequency_months,
                        "exercises": exercises_data,
                        "already_done": bool(evaluation),
                        "done_date": (
                            evaluation.date.strftime("%Y-%m-%d") if evaluation else None
                        ),
                    }
                )

            return success_response(
                msg="Listado de tests para el participante", data=result
            )

        except Exception as e:
            return error_response(f"Internal error: {str(e)}", 500)

    def get_by_external_id(self, external_id):
        try:
            test = Test.query.filter_by(external_id=external_id).first()
            if not test:
                return error_response("Test no encontrado", 404)

            exercises = TestExercise.query.filter_by(test_id=test.id).all()
            exercises_data = [{"name": ex.name, "unit": ex.unit} for ex in exercises]

            data = {
                "external_id": test.external_id,
                "name": test.name,
                "description": test.description,
                "frequency_months": test.frequency_months,
                "exercises": exercises_data,
                "status": test.status,
            }

            return success_response(msg="Detalle del test obtenido", data=data)
        except Exception as e:
            return error_response(f"Error al obtener test: {str(e)}", 500)

    def delete(self, external_id):
        try:
            test = Test.query.filter_by(external_id=external_id).first()
            if not test:
                return error_response(msg="Test no encontrado", code=404)

            test.status = "Activo" if test.status == "Inactivo" else "Inactivo"
            db.session.commit()

            return success_response(
                msg=f"La evaluación ha sido marcado como {test.status} correctamente.",
                code=200,
            )

        except Exception as e:
            db.session.rollback()
            return error_response(
                msg=f"Error interno al intentar eliminar: {str(e)}", code=500
            )
