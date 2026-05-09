"""Генерация запросов по OpenAPI (Schemathesis) — поиск непредвиденных 5xx и сверка ответов со схемой для успешных вызовов."""

import schemathesis
from hypothesis import HealthCheck, settings

from app.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@schema.parametrize()
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_api_contract(case):
    response = case.call()
    assert response.status_code < 500
    if response.status_code < 400:
        case.validate_response(response)
