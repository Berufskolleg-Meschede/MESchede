"""Serialisiertes PLC-I/O, konsistente Snapshots und identitätsgeprüfter Reset."""

import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from app.clients.plc_order_gateway import PlcOrderGateway
from app.domain.order_run import OrderType
from tests.test_opc_ua_client import _make_client, _make_order_tree


@pytest.fixture
def gateway_tree():
    """Verwendet ausschließlich simulierte OPC-UA-Knoten."""
    gateway = PlcOrderGateway('unused-test-url')
    client = _make_client()
    root, header, content, products = _make_order_tree(True)
    header[0].get_value.return_value = 1
    content[1].get_value.return_value = 2
    client.read_status_mes = MagicMock(return_value=5)
    client.read_auftragssteuerung = MagicMock(return_value=1)
    gateway.client = client
    gateway.roots = {kind:root for kind in OrderType}
    try:
        yield gateway,client,root,header,content,products
    finally:
        asyncio.run(gateway.close())


def test_changed_feedback_during_snapshot_is_rejected(gateway_tree):
    gateway,client,*_ = gateway_tree
    client.read_status_mes.side_effect = [1,5]
    with pytest.raises(ValueError,match='änderte sich'):
        asyncio.run(gateway.read(OrderType.PRODUCTION))


def test_reset_clears_inputs_then_count_then_command(gateway_tree):
    gateway,client,root,header,content,products = gateway_tree
    events = []
    for product in products:
        for node in product.get_children():
            node.get_value.return_value = 'old' if node.get_browse_name().Name == 'Produkttext' else 7
    nodes = [node for product in products for node in product.get_children()] + [content[1],header[-1]]
    for node in nodes:
        def record(dv,n=node):
            """Erlaubt echtes Readback nach jedem simulierten Schreibzugriff."""
            events.append((n.get_browse_name().Name,dv.Value.Value))
            n.get_value.return_value = dv.Value.Value
        node.set_data_value.side_effect = record
    asyncio.run(gateway.acknowledge(OrderType.PRODUCTION,1))
    assert events[-2:] == [('Anzahl',0),('Auftragssteuerung_MES',0)]
    assert len(events) == 12
    header[-2].set_data_value.assert_not_called()


def test_foreign_order_is_not_reset_even_with_end_signal(gateway_tree):
    gateway,client,root,header,content,products = gateway_tree
    with pytest.raises(ValueError,match='Auftragsidentität'):
        asyncio.run(gateway.acknowledge(OrderType.PRODUCTION,99))
    for product in products:
        for node in product.get_children():
            node.set_data_value.assert_not_called()
    header[-1].set_data_value.assert_not_called()


def test_failed_count_readback_never_sends_reset_command(gateway_tree):
    gateway,client,root,header,content,products = gateway_tree
    content[1].set_data_value.side_effect = None
    with pytest.raises(ValueError,match='Produktanzahl'):
        asyncio.run(gateway.acknowledge(OrderType.PRODUCTION,1))
    header[-1].set_data_value.assert_not_called()


def test_cancel_waits_for_inflight_io_before_closing_gateway():
    entered,release,completed = threading.Event(),threading.Event(),threading.Event()
    gateway = PlcOrderGateway('unused-test-url')
    def operation():
        """Blockiert gezielt eine synchrone Operation, ohne echten Netzwerkzugriff."""
        entered.set()
        assert release.wait(5)
        completed.set()
    async def scenario():
        """Prüft, dass Cancel kein noch laufendes PLC-Schreiben freigibt."""
        task = asyncio.create_task(gateway._invoke(operation))
        try:
            assert await asyncio.to_thread(entered.wait,2)
            task.cancel()
            await asyncio.sleep(0.01)
            assert not task.done()
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert completed.is_set()
        finally:
            release.set()
            await gateway.close()
    asyncio.run(scenario())
