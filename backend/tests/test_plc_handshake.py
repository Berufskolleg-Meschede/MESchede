import asyncio
from unittest.mock import MagicMock

import pytest

from app.workers import plc_handshake, production_queue, delivery_queue


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 0)


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

    client.write_auftragssteuerung.assert_called_once_with("root", 0)
    client.clear_product_queue.assert_called_once_with("root")
    client.write_anzahl.assert_called_once_with("root", 0)
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

    def cleanup(root):
        assert "StatusMES=5; phase=ready/recovery" in caplog.text

    client.clear_product_queue.side_effect = cleanup
    with caplog.at_level("INFO", logger=plc_handshake.__name__):
        asyncio.run(plc_handshake.wait_for_plc_ready(client, "test-root"))
    client.clear_product_queue.assert_called_once_with("test-root")


def test_done_does_not_treat_initial_idle_feedback_as_completion():
    client = MagicMock()
    events = []
    statuses = iter([0, 1, 5, 5, 0])

    def read_status(root):
        status = next(statuses)
        events.append(("status", status))
        return status

    client.read_status_mes.side_effect = read_status
    client.read_auftragssteuerung.return_value = 0
    client.read_anzahl.return_value = 0
    client.clear_product_queue.side_effect = lambda root: events.append(("queue", 0))
    client.write_anzahl.side_effect = lambda root, value: events.append(("count", value))
    client.write_auftragssteuerung.side_effect = lambda root, value: events.append(("command", value))

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

    client.write_auftragssteuerung.assert_called_once_with("root", 0)


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


@pytest.mark.parametrize("module,queue_name,payload_type,auftragsart", [
    (production_queue, "order_queue", production_queue.ProductionOrderPayload, 1),
    (delivery_queue, "delivery_queue", delivery_queue.DeliveryOrderPayload, 4),
])
@pytest.mark.parametrize("items_per_order", [1, 3])
def test_workers_complete_reset_and_confirm_idle_before_next_order(
    monkeypatch, module, queue_name, payload_type, auftragsart, items_per_order
):
    from datetime import date, time
    from app.models.mes_auftrag import MESAuftrag, AuftragKopf, AuftragInhalt, ProduktDaten

    class SimulatedPLC:
        command = 0
        count = 0
        status = 0
        reset_pending = False

        def __init__(self):
            self.events = []
            self.queue_ids = [9] * 4  # Include stale slots beyond the current order.
            self.dispatched_sizes = []

        async def disconnect(self):
            pass

        def read_auftragssteuerung(self, root):
            return self.command

        def read_anzahl(self, root):
            return self.count

        def clear_product_queue(self, root):
            assert self.status == 5
            self.queue_ids = [0] * len(self.queue_ids)
            self.events.append("clear_queue")

        def write_anzahl(self, root, value):
            assert self.status == 5 and value == 0
            assert not any(self.queue_ids)
            self.count = value
            self.events.append("clear_count")

        def read_status_mes(self, root):
            if self.command == 1:
                self.status = 1 if self.status == 0 else 5
            elif self.reset_pending:
                self.reset_pending = False  # acknowledge on the following poll
            elif self.status == 5:
                self.status = 0
                self.events.append("idle")
            return self.status

        def write_order(self, root, order, kind):
            assert kind == auftragsart
            assert self.command == 0 and self.status == 0
            if self.dispatched_sizes:
                assert self.count == 0 and not any(self.queue_ids)
            assert len(order.inhalt.Produktqueue) == items_per_order
            self.dispatched_sizes.append(len(order.inhalt.Produktqueue))
            for index, item in enumerate(order.inhalt.Produktqueue):
                self.queue_ids[index] = item.ProduktID
            self.command = 1
            self.count = len(order.inhalt.Produktqueue)
            self.events.append(f"start:{order.kopf.Auftragsnummer}")

        def write_auftragssteuerung(self, root, value):
            assert self.status == 5 and value == 0 and self.count == 0
            self.command = 0
            self.reset_pending = True
            self.events.append("reset")

    async def scenario():
        queue = asyncio.Queue()
        monkeypatch.setattr(module, queue_name, queue)
        plc = SimulatedPLC()

        async def create_client():
            return plc

        async def get_root(client):
            return "root"

        monkeypatch.setattr(module, "_create_client", create_client)
        monkeypatch.setattr(module, "_get_root_node", get_root)
        for number in (1, 2):
            queue.put_nowait(payload_type(
                order_id=str(number),
                mes_auftrag=MESAuftrag(
                    kopf=AuftragKopf(
                        Auftragsnummer=number, Startdatum=date(2026, 10, 12), Startzeit=time(8)
                    ),
                    inhalt=AuftragInhalt(Produktqueue=[
                        ProduktDaten(ProduktID=index + 1) for index in range(items_per_order)
                    ]),
                ),
            ))
        task = asyncio.create_task(module._worker_loop())
        try:
            await asyncio.wait_for(queue.join(), timeout=15)
            assert plc.events == ["start:1", "clear_queue", "clear_count", "reset", "idle", "start:2", "clear_queue", "clear_count", "reset", "idle"]
            assert plc.dispatched_sizes == [items_per_order, items_per_order]
            assert plc.count == plc.command == plc.status == 0
            assert not any(plc.queue_ids)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())
