from datetime import date, time
import pytest
from pydantic import ValidationError
from app.models.mes_auftrag import MESAuftrag, AuftragKopf, AuftragInhalt, ProduktDaten


def _make_auftrag() -> MESAuftrag:
    return MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=1,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(8, 0),
        ),
        inhalt=AuftragInhalt(Produktqueue=[ProduktDaten(ProduktID=42)]),
    )


def test_mes_auftrag_defaults():
    order = _make_auftrag()
    assert order.kopf.Prioritaet == 1
    assert order.kopf.Kundennummer == 0
    assert order.kopf.Parameter0 == 0
    assert order.kopf.Parameter1 == 0
    assert order.inhalt.SeriennummerStart == 0


def test_produkt_daten_defaults():
    p = ProduktDaten(ProduktID=1)
    assert p.Produkttext == ""
    assert p.Seriennummer == 0


def test_produkt_queue_populated():
    order = MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=2,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(9, 0),
        ),
        inhalt=AuftragInhalt(
            Produktqueue=[
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1001),
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1002),
            ],
        ),
    )
    assert len(order.inhalt.Produktqueue) == 2
    assert order.inhalt.Produktqueue[0].Seriennummer == 1001


def test_legacy_parameter_input_maps_to_parameter0():
    kopf = AuftragKopf(
        Auftragsnummer=1, Startdatum=date(2026, 10, 12), Startzeit=time(8), Parameter=7
    )
    assert kopf.Parameter0 == 7
    assert "Parameter" not in kopf.model_dump()


@pytest.mark.parametrize("values", [
    {"ProduktID": -1},
    {"ProduktID": 256},
    {"ProduktID": 1, "Seriennummer": 65536},
    {"ProduktID": 1, "Sequenznummer": -1},
    {"ProduktID": 1, "Takt": 65536},
    {"ProduktID": 1, "Produkttext": "x" * 31},
])
def test_product_values_outside_plc_limits_are_rejected(values):
    with pytest.raises(ValidationError):
        ProduktDaten(**values)


def test_empty_product_queue_is_rejected():
    with pytest.raises(ValidationError):
        AuftragInhalt(Produktqueue=[])
