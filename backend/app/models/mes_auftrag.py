from datetime import date, time
from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field


USInt = Annotated[int, Field(ge=0, le=255)]
UInt = Annotated[int, Field(ge=0, le=65535)]


class ProduktDaten(BaseModel):
    ProduktID: USInt
    Produkttext: str = Field(default="", max_length=30)
    Seriennummer: UInt = 0
    Sequenznummer: UInt = 0
    Takt: UInt = 0


class AuftragInhalt(BaseModel):
    # One entry per unit; Anzahl is derived from len(Produktqueue).
    # The writer also checks that every requested slot exists on the PLC.
    Produktqueue: list[ProduktDaten] = Field(min_length=1, max_length=255)
    SeriennummerStart: UInt = 0
    # Inhalt.ProduktID is unused by the PLC; only queue item IDs are written.


class AuftragKopf(BaseModel):
    Auftragsnummer: UInt
    Kundennummer: UInt = 0
    Startdatum: date
    Startzeit: time
    Prioritaet: int = Field(default=1, ge=0, le=2)  # maps to OPC UA node "Priorität"
    Parameter0: USInt = Field(
        default=0, validation_alias=AliasChoices("Parameter0", "Parameter")
    )
    Parameter1: USInt = 0
    # AuftragsArt and Auftragssteuerung_MES are written by the workers.


class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
