"""Модульные тесты: функции проверки данных из validators.py (без базы данных)."""
import pytest

from errors import ValidationError
from validators import (validate_grade, validate_plan, validate_student,
                        validate_study_form, validate_study_year)

STUDENT = {"last_name": "Иванов", "first_name": "Иван", "patronymic": "",
           "admission_year": "2024", "study_form": "дневная", "group_name": "241-326"}
PLAN = {"specialty": "Информационная безопасность", "discipline": "Физика",
        "semester": "2", "hours": "108", "report_form": "экзамен"}


def test_study_form_valid():
    assert validate_study_form("заочная") == "заочная"


def test_study_form_invalid():
    with pytest.raises(ValidationError, match="дневная, вечерняя или заочная"):
        validate_study_form("очная")


def test_student_valid():
    data = validate_student(STUDENT)
    assert data["admission_year"] == 2024
    assert data["patronymic"] is None


@pytest.mark.parametrize("year", ["1989", "2101", "abc"])
def test_student_bad_year(year):
    with pytest.raises(ValidationError, match="Год поступления"):
        validate_student({**STUDENT, "admission_year": year})


def test_student_empty_last_name():
    with pytest.raises(ValidationError, match="Фамилия"):
        validate_student({**STUDENT, "last_name": "  "})


def test_plan_valid():
    data = validate_plan(PLAN)
    assert data["hours"] == 108 and data["semester"] == 2


def test_plan_bad_report_form():
    with pytest.raises(ValidationError, match="экзамен или зачёт"):
        validate_plan({**PLAN, "report_form": "курсовая"})


@pytest.mark.parametrize("field,value", [("semester", "13"), ("hours", "0")])
def test_plan_out_of_range(field, value):
    with pytest.raises(ValidationError):
        validate_plan({**PLAN, field: value})


def test_study_year_valid():
    assert validate_study_year("2025/2026") == "2025/2026"


@pytest.mark.parametrize("value", ["2025", "2025/2027", "25/26"])
def test_study_year_invalid(value):
    with pytest.raises(ValidationError, match="2025/2026"):
        validate_study_year(value)


@pytest.mark.parametrize("grade,form", [("5", "экзамен"), ("2", "экзамен"),
                                        ("зачёт", "зачёт"), ("незачёт", "зачёт")])
def test_grade_valid(grade, form):
    assert validate_grade(grade, form) == grade


@pytest.mark.parametrize("grade,form", [("5", "зачёт"), ("зачёт", "экзамен")])
def test_grade_does_not_match_form(grade, form):
    with pytest.raises(ValidationError, match="допустимы оценки"):
        validate_grade(grade, form)
