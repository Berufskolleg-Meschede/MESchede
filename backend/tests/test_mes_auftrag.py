from datetime import date, time
import pytest
from app.models.mes_auftrag import MESAuftrag, AuftragKopf, AuftragInhalt, ProduktDaten


def _make_auftrag(auftragsart: int = 1) -> MESAuftrag:
    return MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=1,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(8, 0),
            AuftragsArt=auftragsart,
        ),
        inhalt=AuftragInhalt(ProduktID=42, Anzahl=5),
    )


def test_mes_auftrag_defaults():
    order = _make_auftrag()
    assert order.kopf.Prioritaet == 1
    assert order.kopf.Kundennummer == 0
    assert order.kopf.Parameter == 0
    assert order.inhalt.SeriennummerStart == 0
    assert order.inhalt.Produktqueue == []


def test_produkt_daten_defaults():
    p = ProduktDaten()
    assert p.ProduktID == 0
    assert p.Produkttext == ""
    assert p.Seriennummer == 0


def test_produkt_queue_populated():
    order = MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=2,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(9, 0),
            AuftragsArt=4,
        ),
        inhalt=AuftragInhalt(
            ProduktID=7,
            Anzahl=2,
            Produktqueue=[
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1001),
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1002),
            ],
        ),
    )
    assert len(order.inhalt.Produktqueue) == 2
    assert order.inhalt.Produktqueue[0].Seriennummer == 1001
