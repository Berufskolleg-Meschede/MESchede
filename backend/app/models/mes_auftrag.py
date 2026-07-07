from datetime import date, time
from pydantic import BaseModel


class ProduktDaten(BaseModel):
    ProduktID: int
    Produkttext: str = ""
    Seriennummer: int = 0
    Sequenznummer: int = 0
    Takt: int = 0


class AuftragInhalt(BaseModel):
    Produktqueue: list[ProduktDaten]  # one entry per unit; Anzahl is derived from len(Produktqueue)
    SeriennummerStart: int = 0


class AuftragKopf(BaseModel):
    Auftragsnummer: int
    Kundennummer: int = 0
    Startdatum: date
    Startzeit: time
    Prioritaet: int = 1  # 0=Niedrig, 1=Normal, 2=Hoch — maps to OPC UA node "Priorität"
    Parameter: int = 0
    # AuftragsArt and Auftragssteuerung are NOT in the model — workers write them directly


class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
