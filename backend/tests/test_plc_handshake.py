import asyncio
from unittest.mock import MagicMock

import pytest

from app.workers import plc_handshake, production_queue, delivery_queue, order_execution


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 0)
    monkeypatch.setattr(order_execution, "REST_BUFFER_S", 0)


def test_ready_checks_both_command_and_feedback():
    client = MagicMock()
    client.read_status_mes.side_effect = [0, 5, 0]
    client.read_auftragssteuerung.side_effect = [1, 0, 0]

    asyncio.run(plc_handshake.wait_for_plc_ready(client, "root"))

    assert client.read_status_mes.call_count == 3
    client.write_auftragssteuerung.assert_not_called()


def test_ready_acknowledges_a_finished_order_left_after_restart():
    client = MagicMock()
    client.read_status_mes.side_effect = [5, 5, 0]
    client.read_auftragssteuerung.side_effect = [1, 0, 0]
    client.read_anzahl.return_value = 0

    asyncio.run(plc_handshake.wait_for_plc_ready(client, "root"))

    client.write_auftragssteuerung.assert_called_once_with("root", 0, "Kopf", "Auftragssteuerung_MES")
    client.clear_product_queue.assert_called_once_with("root", "Inhalt", "Produktqueue[{index}]")
    client.write_anzahl.assert_called_once_with("root", 0, "Inhalt")
    assert client.read_status_mes.call_count == 3


@pytest.mark.parametrize("last_status", [1, 5])
def test_start_waits_for_feedback_even_if_command_was_sent(last_status):
    client = MagicMock()
    client.read_status_mes.side_effect = [0, 0, last_status]

    asyncio.run(plc_handshake.wait_for_plc_started(client, "root"))

    assert client.read_status_mes.call_count == 3
    client.write_auftragssteuerung.assert_not_called()


@pytest.mark.parametrize("operation,phase", [
    (plc_handshake.wait_for_plc_started, "start"),
    (plc_handshake.wait_for_plc_finished, "completion"),
])
def test_observed_completion_is_explicitly_logged(caplog, operation, phase):
    client = MagicMock()
    client.read_status_mes.side_effect = [0, 5]
    with caplog.at_level("INFO", logger=plc_handshake.__name__):
        assert asyncio.run(operation(client, "test-root")) == 5
    messages = [record.getMessage() for record in caplog.records
                if "PLC completion detected" in record.getMessage()]
    assert len(messages) == 1
    assert f"StatusMES=5; phase={phase}" in messages[0]
    assert "test-root" in messages[0]


def test_recovered_completion_is_logged_before_queue_cleanup(caplog):
    client = MagicMock()
    client.read_status_mes.side_effect = [5, 0]
    client.read_auftragssteuerung.side_effect = [1, 0]
    client.read_anzahl.return_value = 0

    def cleanup(root, inhalt_node=None, produktqueue_pattern=None):
        assert "StatusMES=5; phase=ready/recovery" in caplog.text

    client.clear_product_queue.side_effect = cleanup
    with caplog.at_level("INFO", logger=plc_handshake.__name__):
        asyncio.run(plc_handshake.wait_for_plc_ready(client, "test-root"))
    client.clear_product_queue.assert_called_once_with("test-root", "Inhalt", "Produktqueue[{index}]")


def test_done_does_not_treat_initial_idle_feedback_as_completion():
    client = MagicMock()
    events = []
    statuses = iter([0, 1, 5, 5, 0])

    def read_status(root, feedback_node=None, status_node=None):
        status = next(statuses)
        events.append(("status", status))
        return status

    client.read_status_mes.side_effect = read_status
    client.read_auftragssteuerung.return_value = 0
    client.read_anzahl.return_value = 0
    client.clear_product_queue.side_effect = (
        lambda root, inhalt_node=None, produktqueue_pattern=None: events.append(("queue", 0))
    )
    client.write_anzahl.side_effect = (
        lambda root, value, inhalt_node=None: events.append(("count", value))
    )
    client.write_auftragssteuerung.side_effect = (
        lambda root, value, kopf_node=None, auftragssteuerung_node=None: events.append(("command", value))
    )

    asyncio.run(plc_handshake.wait_for_plc_done(client, "root"))

    assert events == [
        ("status", 0), ("status", 1), ("status", 5),
        ("queue", 0), ("count", 0), ("command", 0), ("status", 5), ("status", 0),
    ]


def test_completion_timeout_does_not_reset_an_unfinished_order():
    client = MagicMock()
    client.read_status_mes.return_value = 1

    with pytest.raises(TimeoutError, match="completion.*got 1"):
        asyncio.run(plc_handshake.wait_for_plc_done(client, "root", timeout_s=0))

    client.write_auftragssteuerung.assert_not_called()
    client.write_anzahl.assert_not_called()
    client.clear_product_queue.assert_not_called()


def test_reset_timeout_does_not_report_success():
    client = MagicMock()
    client.read_status_mes.return_value = 5
    client.read_auftragssteuerung.return_value = 0
    client.read_anzahl.return_value = 0

    with pytest.raises(TimeoutError, match="PLC reset timeout.*status=5"):
        asyncio.run(plc_handshake.wait_for_plc_done(client, "root", reset_timeout_s=0))

    client.write_auftragssteuerung.assert_called_once_with("root", 0, "Kopf", "Auftragssteuerung_MES")


def test_failed_queue_cleanup_keeps_count_and_command_latched():
    client = MagicMock()
    client.read_status_mes.return_value = 5
    client.clear_product_queue.side_effect = ValueError("queue reset readback mismatch")
    with pytest.raises(ValueError, match="queue reset readback mismatch"):
        asyncio.run(plc_handshake.wait_for_plc_done(client, "root"))
    client.write_anzahl.assert_not_called()
    client.write_auftragssteuerung.assert_not_called()


def test_start_timeout_is_reported():
    client = MagicMock()
    client.read_status_mes.return_value = 0

    with pytest.raises(TimeoutError, match="start.*got 0"):
        asyncio.run(plc_handshake.wait_for_plc_started(client, "root", timeout_s=0))
