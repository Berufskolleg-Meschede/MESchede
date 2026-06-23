from datetime import date, time
from pydantic import BaseModel


class ProduktDaten(BaseModel):
    Produkttext: str = ""
    ProduktID: int = 0
    Seriennummer: int = 0
    Sequenznummer: int = 0
    Takt: int = 0


class AuftragInhalt(BaseModel):
    ProduktID: int
    Anzahl: int
    SeriennummerStart: int = 0
    Produktqueue: list[ProduktDaten] = []


class AuftragKopf(BaseModel):
    Auftragsnummer: int
    Kundennummer: int = 0
    Startdatum: date
    Startzeit: time
    AuftragsArt: int  # 1=Produktion, 4=Kommissionieren
    Prioritaet: int = 1  # 0=Niedrig, 1=Normal, 2=Hoch — maps to OPC UA node "Priorität"
    Parameter: int = 0
    # Auftragssteuerung is NOT in the model — worker writes it directly


class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
