from datetime import date, time
import pytest
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
    assert order.kopf.Parameter == 0
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
