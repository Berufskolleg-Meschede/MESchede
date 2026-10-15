"""Echte HTTP-Verträge ohne Anlagenzugriff und ohne Projektkonfiguration."""

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.domain.order_run import OrderType
from app.main import create_app
from app.routers import productionorders_router,deliveryorders_router,orders_router
from app.settings import OrderSettings
from app.workers.order_worker_host import OrderWorkerHost
from app.repositories.product_catalog_repository import ProductCatalogRepository
from app.models.order_input import CatalogProduct, OrderCatalog
from datetime import datetime, timezone
from tests.order_fakes import FakeLeadership,SimulatedGateway
from tests.test_order_services import running_order


def client_for(repository):
    """Injiziert den echten Repository; GET und Reviews verbinden niemals zur PLC."""
    gateway = SimulatedGateway()
    seed_catalog(repository)
    host = OrderWorkerHost(repository,gateway,OrderSettings(),FakeLeadership())
    host.task = MagicMock()
    host.task.done.return_value = False
    application = FastAPI()
    application.state.order_worker = host
    for router in (productionorders_router.router,deliveryorders_router.router,orders_router.router):
        application.include_router(router)
    return TestClient(application),gateway


def seed_catalog(repository):
    """Speichert ausdrücklich synthetische Produktdaten als Voraussetzung der Annahme."""
    for kind in OrderType:
        ProductCatalogRepository(repository.engine).save(kind, OrderCatalog(
            products=[CatalogProduct(product_id=1, product_text="Testprodukt")],
            capacity=33, observed_at=datetime.now(timezone.utc),
        ))


def test_pages_filter_before_pagination_and_share_global_review(order_repository,order_payload):
    stored = running_order(order_repository,order_payload(1,'1'))
    order_repository.require_review(stored.run.id,'Testunterbrechung')
    order_repository.admit(OrderType.PRODUCTION,order_payload(2,'2'))
    order_repository.admit(OrderType.DELIVERY,order_payload(3,'3'))
    client,gateway = client_for(order_repository)
    page = client.get('/productionorder/',params={'search':' 0002 ','limit':1}).json()
    assert page['filtered_total'] == 1 and page['total'] == 2
    assert page['orders'][0]['order_id'] == '2'
    assert page['summary']['review_required'] == 1
    delivery = client.get('/deliveryorder/').json()
    assert [item['order_type'] for item in delivery['orders']] == ['delivery']
    assert delivery['reviews'][0]['order_type'] == 'production'
    assert delivery['waiting'][0]['queue_position'] == 2
    overview = client.get('/orders/overview').json()
    assert overview['combined']['total'] == 3
    assert overview['dispatch']['blocked']
    assert gateway.reads == 0 and gateway.events == []


@pytest.mark.parametrize('amount',[-1,1.5,True,3])
def test_review_http_rejects_invalid_quantities(order_repository,order_payload,amount):
    stored = running_order(order_repository,order_payload())
    order_repository.require_review(stored.run.id,'Testunterbrechung')
    version = order_repository.snapshot().orders[0].run.version
    client,gateway = client_for(order_repository)
    response = client.post(f'/orders/runs/{stored.run.id}/reviews',json={
        'request_id':str(uuid4()),'expected_version':version,'outcome':'completed','good_quantity':amount,
    })
    assert response.status_code == 422
    assert order_repository.snapshot().orders[0].run.review_required
    assert gateway.events == []


def test_http_review_without_note_is_idempotent_and_keeps_reservation(order_repository,order_payload):
    stored = running_order(order_repository,order_payload())
    order_repository.require_review(stored.run.id,'Testunterbrechung')
    client,gateway = client_for(order_repository)
    payload = {'request_id':str(uuid4()),'expected_version':order_repository.snapshot().orders[0].run.version,'outcome':'completed'}
    endpoint = f'/orders/runs/{stored.run.id}/reviews'
    first = client.post(endpoint,json=payload)
    assert first.status_code == 200
    assert client.post(endpoint,json=payload).json() == first.json()
    assert client.post(endpoint,json={**payload,'request_id':str(uuid4())}).status_code == 409
    view = client.get('/productionorder/test-1').json()
    assert view['has_manual_review'] and view['good_quantity'] is None
    assert order_repository.snapshot().dispatch.active_run_id == stored.run.id
    assert gateway.events == []


def test_injected_app_lifespan_works_without_live_plc(order_repository,order_payload):
    seed_catalog(order_repository)
    gateway = SimulatedGateway()
    host = OrderWorkerHost(order_repository,gateway,OrderSettings(),FakeLeadership())
    with TestClient(create_app(host)) as client:
        response = client.post('/deliveryorder/',json=order_payload().model_dump(mode='json'))
        assert response.status_code == 202
        assert client.get('/orders/overview').json()['delivery']['pending'] == 1
    assert gateway.closed and not host.running
    assert gateway.events == []
