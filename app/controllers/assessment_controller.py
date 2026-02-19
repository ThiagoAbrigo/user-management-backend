from app.models.assessment import Assessment
from app.models.participant import Participant
from app.services.activity_service import log_activity
from app.utils.responses import error_response, success_response
from app import db
from sqlalchemy import func

from app.utils.validations.assessment_validation import (
    validate_numeric_fields,
    validate_ranges,
    validate_required_fields,
)

VALIDATION_ERROR_MSG = "Error de validación"
INTERNAL_ERROR_MSG = "Error interno del servidor"


class AssessmentController:
    def classify_bmi_adult(self, bmi):
        if bmi < 18.5:
            return "Bajo peso"
        elif bmi < 25:
            return "Peso adecuado"
        elif bmi < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"

    def calculate_bmi(self, weight, height):
        if height <= 0 or weight <= 0:
            return None
        return round(weight / (height**2), 2)

    def get_assessment(self):
        try:
            assessments = Assessment.query.all()

            data = [
                {
                    "external_id": a.external_id,
                    "participant_external_id": a.participant.external_id,
                    "participant_name": f"{a.participant.firstName} {a.participant.lastName}",
                    "dni": a.participant.dni,
                    "age": a.participant.age,
                    "date": a.date,
                    "weight": a.weight,
                    "height": a.height,
                    "waistPerimeter": a.waistPerimeter,
                    "bmi": a.bmi,
                    "status": a.status,
                }
                for a in assessments
            ]

            return success_response(
                msg="Evaluaciones listadas correctamente", data=data, code=200
            )

        except Exception as e:
            return error_response(msg=f"Error interno del servidor: {str(e)}", code=500)

    def register(self, data):
        try:
            errors = {}

            # 1. Validaciones básicas
            errors.update(validate_required_fields(data))

            participant_external_id = data.get("participant_external_id")
            weight = data.get("weight")
            height = data.get("height")

            waist = data.get("waistPerimeter")
            arm = data.get("armPerimeter")
            leg = data.get("legPerimeter")
            calf = data.get("calfPerimeter")

            # 2. Validar tipos numéricos
            errors.update(
                validate_numeric_fields(
                    {
                        "weight": weight,
                        "height": height,
                        "waistPerimeter": waist,
                        "armPerimeter": arm,
                        "legPerimeter": leg,
                        "calfPerimeter": calf,
                    }
                )
            )

            # 3. Validar rangos
            errors.update(validate_ranges(weight, height, waist, arm, leg, calf))

            # 4. Retornar errores si existen
            if errors:
                return error_response(
                    msg=VALIDATION_ERROR_MSG,
                    errors=errors,
                    code=400,
                )

            # 5. Buscar participante
            participant = Participant.query.filter_by(
                external_id=participant_external_id
            ).first()

            if not participant:
                return error_response(
                    msg=VALIDATION_ERROR_MSG,
                    errors={"participant_external_id": "Participante no encontrado"},
                    code=400,
                )

            # 6. Calcular IMC
            bmi = self.calculate_bmi(weight, height)
            status = self.classify_bmi_adult(bmi)

            # 7. Crear evaluación
            assessment = Assessment(
                participant_id=participant.id,
                weight=weight,
                height=height,
                waistPerimeter=waist,
                armPerimeter=arm,
                legPerimeter=leg,
                calfPerimeter=calf,
                bmi=bmi,
                status=status,
            )

            db.session.add(assessment)

            log_activity(
                type="MEDICION",
                title="Medición registrada",
                description=(
                    f"Se registró una evaluación para "
                    f"{participant.firstName} {participant.lastName}"
                ),
            )

            db.session.commit()

            return success_response(
                msg="Medida antropométrica registrada exitosamente",
                data={
                    "external_id": assessment.external_id,
                    "participant_external_id": participant.external_id,
                    "bmi": assessment.bmi,
                    "status": assessment.status,
                },
                code=200,
            )

        except Exception as e:
            db.session.rollback()
            return error_response(
                msg=f"Error interno del servidor: {str(e)}",
                code=500,
            )

    def get_participants_external_id(self, participant_external_id):
        try:
            participant = Participant.query.filter_by(
                external_id=participant_external_id
            ).first()

            if not participant:
                return error_response(
                    msg="Error de validación",
                    errors={"participant_external_id": "Participante no encontrado"},
                    code=400,
                )

            assessments = (
                Assessment.query.filter_by(participant_id=participant.id)
                .order_by(Assessment.date.desc())
                .all()
            )

            data = [
                {
                    "external_id": a.external_id,
                    "date": a.date,
                    "weight": a.weight,
                    "height": a.height,
                    "waistPerimeter": a.waistPerimeter,
                    "armPerimeter": a.armPerimeter,
                    "legPerimeter": a.legPerimeter,
                    "calfPerimeter": a.calfPerimeter,
                    "bmi": a.bmi,
                    "status": a.status,
                }
                for a in assessments
            ]

            return success_response(
                msg="Evaluaciones del participante listadas correctamente",
                data={
                    "participant": {
                        "external_id": participant.external_id,
                        "firstName": f"{participant.firstName} {participant.lastName}",
                        "dni": participant.dni,
                        "age": participant.age,
                        "status": participant.status,
                    },
                    "assessments": data,
                },
            )

        except Exception as e:
            return error_response(msg=f"Error interno del servidor: {str(e)}", code=500)
