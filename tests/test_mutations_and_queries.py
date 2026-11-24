"""Тесты бизнес-операций (Mutation), фильтрации, сортировки и агрегации (ЛР № 4)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.app import create_app
from gateway.clients.mocks import build_mock_clients


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    app = create_app(clients=build_mock_clients())
    tc = TestClient(app)
    login_resp = tc.post(
        "/auth/login", json={"email": "orlova@bank.local", "password": "admin_pass123"}
    )
    assert login_resp.status_code == 200
    tc.headers["Authorization"] = f"Bearer {login_resp.json()['access_token']}"
    return tc


def _gql(client: TestClient, query: str, variables: dict | None = None) -> dict:
    resp = client.post("/graphql", json={"query": query, "variables": variables or {}})
    assert resp.status_code == 200
    return resp.json()


def test_filtering_sorting_and_aggregation(client: TestClient):
    query = """
    query {
      filtered: hypotheses(
        filter: { productId: "prod-001", priority: P1, minRiceScore: 100.0 }
        sort: { field: RICE_SCORE, direction: DESC }
      ) {
        id
        title
        priority
        riceScore { calculatedScore }
      }
      summary: hypothesesSummary {
        totalCount
        avgRiceScore
        maxRiceScore
        confirmedRate
        inBacklogCount
        byStatus { status count }
        byPriority { priority count }
      }
    }
    """
    body = _gql(client, query)
    assert "errors" not in body
    filtered = body["data"]["filtered"]
    assert len(filtered) >= 1
    assert all(h["priority"] == "P1" for h in filtered)
    assert all(h["riceScore"]["calculatedScore"] >= 100.0 for h in filtered)

    summary = body["data"]["summary"]
    assert summary["totalCount"] >= 3
    assert summary["maxRiceScore"] >= 144.0
    assert len(summary["byStatus"]) >= 1
    assert len(summary["byPriority"]) >= 1


def test_full_business_lifecycle_mutations(client: TestClient):
    create_hyp = """
    mutation {
      createHypothesis(input: {
        title: "Быстрый перевод по QR в приложении"
        description: "Добавить кнопку сканирования QR на главный экран"
        productId: "prod-001"
        ownerId: "user-001"
        priority: P1
        ifAction: "показать кнопку QR на главном экране"
        thenResult: "доля переводов по QR вырастет на 15%"
        becauseAssumption: "пользователи тратят лишние шаги на поиск раздела"
      }) {
        id
        status
        priority
        template { ifAction }
      }
    }
    """
    b1 = _gql(client, create_hyp)
    assert "errors" not in b1
    hyp_id = b1["data"]["createHypothesis"]["id"]
    assert b1["data"]["createHypothesis"]["status"] == "DRAFT"

    calc_rice = f"""
    mutation {{
      calculateRICE(input: {{
        hypothesisId: "{hyp_id}", reach: 500, impact: 2.0, confidence: 0.9, effort: 5
      }}) {{
        calculatedScore
      }}
    }}
    """
    b2 = _gql(client, calc_rice)
    assert "errors" not in b2
    assert b2["data"]["calculateRICE"]["calculatedScore"] == 180.0

    create_res = f"""
    mutation {{
      createResearch(input: {{
        hypothesisId: "{hyp_id}"
        title: "Юзабилити-тест кнопки QR"
        type: "QUALITATIVE"
        method: "Модерируемое интервью"
        targetAudience: "Активные клиенты"
        sampleSize: 12
        assigneeId: "user-002"
        goal: "Проверить заметность кнопки"
        questions: "Находит ли пользователь кнопку за 5 секунд?"
        successCriteria: "80% респондентов находят сразу"
      }}) {{
        id
        status
      }}
    }}
    """
    b3 = _gql(client, create_res)
    assert "errors" not in b3
    res_id = b3["data"]["createResearch"]["id"]
    assert b3["data"]["createResearch"]["status"] == "PLANNED"

    b_note = _gql(
        client,
        f'mutation {{ addResearchNote(input: {{ researchId: "{res_id}", text: "Респондент сразу заметил кнопку" }}) {{ id }} }}',
    )
    assert "errors" not in b_note

    b_ins = _gql(
        client,
        f'mutation {{ addInsight(input: {{ researchId: "{res_id}", text: "10 из 12 участников успешно оплатили по QR" }}) {{ id }} }}',
    )
    assert "errors" not in b_ins

    pub_rep = f"""
    mutation {{
      publishReport(input: {{
        researchId: "{res_id}"
        conclusion: "CONFIRMED"
        recommendations: "Выкатить на 100% аудитории"
      }}) {{
        id
        conclusion
      }}
    }}
    """
    b4 = _gql(client, pub_rep)
    assert "errors" not in b4

    apply_res = f"""
    mutation {{
      applyResearchResult(input: {{
        hypothesisId: "{hyp_id}"
        researchId: "{res_id}"
        status: CONFIRMED
      }}) {{
        id
        status
      }}
    }}
    """
    b5 = _gql(client, apply_res)
    assert "errors" not in b5
    assert b5["data"]["applyResearchResult"]["status"] == "CONFIRMED"

    exp_res = f"""
    mutation {{
      exportToBacklog(input: {{ hypothesisId: "{hyp_id}" }}) {{
        externalSystem
        externalKey
        status
      }}
    }}
    """
    b6 = _gql(client, exp_res)
    assert "errors" not in b6
    assert b6["data"]["exportToBacklog"]["externalSystem"] == "TASK_TRACKER"

    rm_res = f"""
    mutation {{
      scheduleOnRoadmap(input: {{
        hypothesisId: "{hyp_id}"
        startDate: "2026-11-01"
        endDate: "2026-11-10"
      }}) {{
        duration
        hypothesisTitle
      }}
    }}
    """
    b7 = _gql(client, rm_res)
    assert "errors" not in b7
    assert b7["data"]["scheduleOnRoadmap"]["duration"] == 10

    cmt_res = f"""
    mutation {{
      addComment(input: {{
        entityType: HYPOTHESIS
        entityId: "{hyp_id}"
        text: "Передано в разработку"
      }}) {{
        id
        text
      }}
    }}
    """
    b8 = _gql(client, cmt_res)
    assert "errors" not in b8


def test_submit_idea_and_business_rule_errors(client: TestClient):
    idea_mut = """
    mutation {
      submitIdea(input: {
        productId: "prod-002"
        title: "Виджет лимитов по карте"
        description: "Показывать остаток дневного лимита на главном экране"
        expectedEffect: "Снижение обращений в поддержку на 10%"
        category: "Дебетовые карты"
        authorName: "Мария Соколова (поддержка)"
      }) {
        id
        status
        hypothesisId
      }
    }
    """
    b_idea = _gql(client, idea_mut)
    assert "errors" not in b_idea
    assert b_idea["data"]["submitIdea"]["status"] == "CONVERTED"
    new_hyp_id = b_idea["data"]["submitIdea"]["hypothesisId"]
    assert new_hyp_id is not None

    b_bad_exp = _gql(
        client,
        f'mutation {{ exportToBacklog(input: {{ hypothesisId: "{new_hyp_id}" }}) {{ externalKey }} }}',
    )
    assert "errors" in b_bad_exp

    b_bad_rice = _gql(
        client,
        f'mutation {{ calculateRICE(input: {{ hypothesisId: "{new_hyp_id}", reach: 100, impact: 2.0, confidence: 1.5, effort: 3 }}) {{ calculatedScore }} }}',
    )
    assert "errors" in b_bad_rice

    b_bad_apply = _gql(
        client,
        'mutation { applyResearchResult(input: { hypothesisId: "hyp-001", researchId: "res-001", status: CONFIRMED }) { id } }',
    )
    assert "errors" in b_bad_apply
