"""End-to-End-Dispatch über gemeinsame PostgreSQL-Reservierung und simulierte PLC."""

import asyncio
from dataclasses import replace

from app.domain.order_run import OrderType, RunPhase
from app.services.order_dispatch_service import OrderDispatchService
from app.settings import OrderSettings
from tests.order_fakes import FakeLeadership, SimulatedGateway


def test_production_and_delivery_complete_in_global_fifo_order(order_repository, order_payload):
    order_repository.admit(OrderType.DELIVERY, order_payload(1))
    order_repository.admit(OrderType.PRODUCTION, order_payload(2))
    gateway = SimulatedGateway(order_repository)
    service = OrderDispatchService(order_repository, gateway, OrderSettings(
        contract_verified=True, product_results={11: "good", 12: "failed"}, rest_buffer_s=0,
    ), FakeLeadership())

    async def scenario():
        """Lässt Endresultate und Reset vor dem nächsten Start nachweisen."""
        for kind in (OrderType.DELIVERY, OrderType.PRODUCTION):
            await service.tick(gateway.snapshots)
            await service.tick(gateway.snapshots)
            gateway.snapshots[kind] = replace(gateway.snapshots[kind], status=5)
            await service.tick(gateway.snapshots)
            await service.tick(gateway.snapshots)

    asyncio.run(scenario())
    assert gateway.events == [
        ("start", OrderType.DELIVERY, 1), ("ack", OrderType.DELIVERY),
        ("start", OrderType.PRODUCTION, 2), ("ack", OrderType.PRODUCTION),
    ]
    assert all(item.run.phase == RunPhase.COMPLETED.value for item in order_repository.snapshot().orders)


def test_ready_order_starts_without_a_product_result_mapping(order_repository, order_payload):
    order_repository.admit(OrderType.PRODUCTION, order_payload())
    gateway = SimulatedGateway()
    service = OrderDispatchService(order_repository, gateway, OrderSettings(rest_buffer_s=0), FakeLeadership())
    asyncio.run(service.tick(gateway.snapshots))
    assert gateway.events == [("start", OrderType.PRODUCTION, 1)]
