from datetime import date, time
from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field, field_validator


USInt = Annotated[int, Field(strict=True, ge=0, le=255)]
UInt = Annotated[int, Field(strict=True, ge=0, le=65535)]


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
    Prioritaet: int = Field(default=1, strict=True, ge=0, le=2)  # maps to OPC UA node "Priorität"
    Parameter0: USInt = Field(
        default=0, validation_alias=AliasChoices("Parameter0", "Parameter")
    )
    Parameter1: USInt = 0
    # AuftragsArt and Auftragssteuerung_MES are written by the workers.

    @field_validator("Startdatum")
    @classmethod
    def validate_start_date(cls, value: date) -> date:
        """Lehnt Daten außerhalb des vom Writer unterstützten SIMATIC-DATE-Bereichs ab."""
        if not date(1990, 1, 1) <= value <= date(2168, 12, 31):
            raise ValueError("Das Startdatum muss zwischen 01.01.1990 und 31.12.2168 liegen.")
        return value

    @field_validator("Startzeit")
    @classmethod
    def validate_start_time(cls, value: time) -> time:
        """Verlangt lokale Anlagenzeit ohne einen vom PLC-Writer abgelehnten Offset."""
        if value.tzinfo is not None:
            raise ValueError("Die Startzeit muss lokale Anlagenzeit ohne Zeitzonenoffset sein.")
        return value


class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
