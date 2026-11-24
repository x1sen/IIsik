"""Тесты изолированных внутренних сервисов и их баз данных."""

from __future__ import annotations

import pytest

from gateway.clients.mocks import build_mock_clients
from shared.exceptions import EntityNotFoundError, ValidationError


@pytest.fixture()
def clients(tmp_path, monkeypatch):
    monkeypatch.setenv("PDP_DATA_DIR", str(tmp_path))
    return build_mock_clients()


def test_hypothesis_service_read_and_duplicates(clients):
    items = clients.hypothesis.list_hypotheses()
    assert len(items) == 3

    hyp = clients.hypothesis.get_hypothesis("hyp-001")
    assert hyp.priority == "P1"
    assert clients.hypothesis.get_template("hyp-001") is not None
    assert clients.hypothesis.get_rice_score("hyp-001").calculated_score == 144.0
    assert len(clients.hypothesis.list_comments("HYPOTHESIS", "hyp-001")) == 2

    dups = clients.hypothesis.find_duplicate_hypotheses(
        title="Упрощение анкеты онлайн-кредита",
        description="Сокращение полей заявки на онлайн-кредит",
        product_id="prod-001",
    )
    assert len(dups) >= 1
    assert dups[0].hypothesis_id == "hyp-001"


def test_hypothesis_not_found_and_validation_errors(clients):
    with pytest.raises(EntityNotFoundError):
        clients.hypothesis.get_hypothesis("hyp-999")

    with pytest.raises(ValidationError):
        clients.hypothesis.find_duplicate_hypotheses("   ", "", "prod-001")


def test_other_services_read_seeded_data(clients):
    assert clients.research.get_research("res-001").hypothesis_id == "hyp-001"
    assert clients.report.get_report_by_research("res-002") is not None
    assert len(clients.roadmap.list_roadmap()) == 2
    assert len(clients.analytics.get_dashboard_metrics(product_id="prod-001")) == 2
    assert clients.product.get_product("prod-001").name == "Онлайн-кредитование"
    assert clients.user.get_user("user-002").role == "CX_EXPERT"
    assert len(clients.notification.list_notifications("user-001", unread_only=True)) == 1
    assert len(clients.idea_portal.list_ideas()) == 1
    assert len(clients.file_storage.list_attachments("RESEARCH", "res-001")) == 1
    assert len(clients.audit.list_activity_logs("HYPOTHESIS", "hyp-001")) == 2
    assert clients.integration.get_backlog_task("hyp-002").external_key == "PD-412"
