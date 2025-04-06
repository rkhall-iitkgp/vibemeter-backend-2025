from fastapi import APIRouter

from app.utils.helpers import extract_columns_by_employee_id, format_response

router = APIRouter()


@router.get("/{employee_id}")
def get_data(employee_id: str):
    return format_response(
        extract_columns_by_employee_id(
            "app/models/employee_targeting_results_results.csv", employee_id
        )
    )
