"""Фаззинг входов через Hypothesis: сервер не должен отвечать 5xx на произвольные, но типичные данные."""

from hypothesis import HealthCheck, given, settings, strategies as st

safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), max_codepoint=0xFFFF),
    max_size=256,
)


@given(safe_text)
@settings(max_examples=60, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_health_query_params_never_500(client, q):
    r = client.get("/health", params={"x": q})
    assert r.status_code == 200


@given(safe_text)
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_products_list_extra_query_never_500(client, q):
    r = client.get("/api/products", params={"noise": q})
    assert r.status_code == 200


@given(st.binary(min_size=0, max_size=2048))
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_products_post_random_body_not_server_error(client, raw):
    r = client.post(
        "/api/products",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code < 500


json_primitive = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | safe_text
)

json_tree = st.recursive(
    json_primitive,
    lambda children: st.lists(children, max_size=6) | st.dictionaries(safe_text, children, max_size=6),
    max_leaves=40,
)


@given(json_tree)
@settings(max_examples=60, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_products_post_json_tree_not_server_error(client, value):
    r = client.post("/api/products", json=value)
    assert r.status_code < 500


@given(st.integers(min_value=-1_000_000_000, max_value=1_000_000_000))
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_nested_path_ids_not_server_error(client, n):
    r = client.get(f"/api/products/{n}")
    assert r.status_code in (200, 404, 422)
