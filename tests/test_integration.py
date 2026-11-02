"""Интеграционные тесты: разделы приложения вместе с PostgreSQL.

Перед запуском база должна быть создана из db/schema.sql и db/seed.sql,
адрес базы передаётся в переменной окружения DATABASE_URL.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"),
                                reason="нужна база PostgreSQL (DATABASE_URL)")


def page(response):
    return response.get_data(as_text=True)


def test_count_students_by_form(client):
    """Функция 1: в seed.sql два студента заочной формы."""
    response = client.get("/dean/students?study_form=заочная")
    assert response.status_code == 200
    assert "<strong>2</strong>" in page(response)


def test_count_students_bad_form(client):
    response = client.get("/dean/students?study_form=очная")
    assert response.status_code == 400
    assert "дневная, вечерняя или заочная" in page(response)


def test_discipline_hours(client):
    """Функция 2: «Дискретная математика» – 108 ч (экзамен) и 72 ч (зачёт)."""
    response = client.get("/student/?discipline=Дискретная математика")
    text = page(response)
    assert response.status_code == 200
    assert "<strong>180</strong>" in text
    assert "экзамен" in text and "зачёт" in text


def test_discipline_not_found(client):
    response = client.get("/student/?discipline=Астрономия")
    assert response.status_code == 404
    assert "нет в учебном плане" in page(response)


def test_add_student(client):
    """Функция 3: новый студент сохраняется и появляется в списке."""
    form = {"last_name": "Тестов", "first_name": "Пётр", "patronymic": "",
            "admission_year": "2025", "study_form": "вечерняя", "group_name": "251-326"}
    response = client.post("/dean/students/new", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "Студент добавлен" in page(response)
    assert "Тестов" in page(response)


def test_add_student_bad_year_not_saved(client):
    form = {"last_name": "Неверов", "first_name": "Иван", "patronymic": "",
            "admission_year": "1989", "study_form": "дневная", "group_name": "241-326"}
    response = client.post("/dean/students/new", data=form)
    assert response.status_code == 400
    assert "от 1990 до 2100" in page(response)
    assert "Неверов" not in page(client.get("/dean/students"))


def test_edit_missing_student(client):
    response = client.get("/dean/students/999/edit")
    assert response.status_code == 404
    assert "не найден" in page(response)


def test_add_grade(client):
    """Функция 4: оценка по экзамену сохраняется в журнале."""
    form = {"study_year": "2025/2026", "student_id": "6", "plan_id": "5", "grade": "4"}
    response = client.post("/teacher/grades/new", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "Оценка добавлена в журнал" in page(response)


def test_grade_must_match_report_form(client):
    form = {"study_year": "2025/2026", "student_id": "6", "plan_id": "4", "grade": "5"}
    response = client.post("/teacher/grades/new", data=form)
    assert response.status_code == 400
    assert "Для формы «зачёт» допустимы оценки" in page(response)


def test_duplicate_grade_rejected(client):
    form = {"study_year": "2024/2025", "student_id": "1", "plan_id": "2", "grade": "4"}
    response = client.post("/teacher/grades/new", data=form)
    assert response.status_code == 400
    assert "уже есть оценка" in page(response)


def test_student_average_grade(client):
    """У Иванова одна экзаменационная оценка «5» и один зачёт – средний балл 5.0."""
    response = client.get("/student/?student_id=1")
    assert response.status_code == 200
    assert "Средний балл: <strong>5.0</strong>" in page(response)


def test_error_hook_writes_log(client):
    """Хук пользовательских исключений записывает ошибку в logs/app.log."""
    client.get("/dean/students?study_form=очная")
    with open("logs/app.log", encoding="utf-8") as log:
        assert "ValidationError" in log.read()
