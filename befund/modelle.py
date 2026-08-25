"""Typisierte Ergebnisformen.

Jedes Werkzeug gibt ein Pydantic-Modell zurueck, kein Dict. Zwei Gruende:
das Sprachmodell bekommt eine Form, die es nicht missverstehen kann, und die
Oberflaeche bekommt einen Vertrag, der sich nicht still aendert.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Status = Literal["documented", "unexplained", "suspected_violation", "not_assessable"]


class Ereignis(BaseModel):
    """Ein Prozessschritt aus dem ERP-Log."""
    zeit: datetime
    aktivitaet: str
    wer: Optional[str] = None
    rolle: Optional[str] = None
    genehmigungsgrenze_eur: Optional[float] = None


class Beleg(BaseModel):
    """Ein Dokument aus dem Korpus."""
    id: str
    typ: str
    pfad: Optional[str] = None
    text: Optional[str] = None


class Klausel(BaseModel):
    """Die Vertragsklausel, gegen die geprueft wird."""
    vertrag: str
    paragraf: Optional[str] = None
    titel: Optional[str] = None
    ankuendigungsfrist_tage: Optional[int] = None
    toleranz_prozent: Optional[float] = None


class Befugnis(BaseModel):
    """Freigabebefugnis einer Person laut Freigabematrix."""
    kennung: Optional[str] = None
    name: str
    rolle: Optional[str] = None
    email: Optional[str] = None
    genehmigungsgrenze_eur: float = 0.0
    zahlfreigabe_grenze_eur: float = 0.0


class Treffer(BaseModel):
    """Ein Chunk-Treffer aus der Vektorsuche."""
    chunk_id: str
    dokument_id: str
    dokument_typ: str
    score: float
    text: str


class POItemKontext(BaseModel):
    """Die vollstaendige Beweislage zu einer Bestellposition."""
    poitem: str
    po: str
    position: Optional[str] = None
    wert_eur: float = 0.0
    bestelldatum: Optional[datetime] = None
    warengruppe_key: Optional[str] = None
    warengruppe: Optional[str] = None
    spend_area: Optional[str] = None
    prozessvariante: Optional[str] = None
    lieferant: Optional[str] = None
    vendor_id: Optional[str] = None
    lieferant_ort: Optional[str] = None
    klausel: Optional[Klausel] = None
    ereignisse: list[Ereignis] = Field(default_factory=list)
    belege: list[Beleg] = Field(default_factory=list)
    findings: list[dict] = Field(default_factory=list)

    @property
    def preisaenderungen(self) -> list[Ereignis]:
        return [e for e in self.ereignisse if e.aktivitaet == "Change Price"]


class Fakten(BaseModel):
    """Die aus Beleg und Graph berechneten Zahlen. Nichts hiervon stammt vom Modell."""
    preis_geaendert_am: Optional[datetime] = None
    geaendert_durch: Optional[Befugnis] = None
    tage_nach_bestellung: Optional[int] = None
    ankuendigung_am: Optional[date] = None
    wirksam_ab: Optional[date] = None
    vorlauf_tage: Optional[int] = None
    erhoehung_prozent: Optional[float] = None
    quelle_beleg: Optional[str] = None


class Befund(BaseModel):
    """Das Urteil. Status und Gruende sind berechnet, nicht generiert."""
    status: Status
    gruende: list[str] = Field(default_factory=list)
    ueber_befugnis: bool = False
    belege: list[str] = Field(default_factory=list)


class Bericht(BaseModel):
    """Das Objekt, aus dem die einseitige PDF gerendert wird."""
    kontext: POItemKontext
    fakten: Fakten
    befund: Befund
    erlaeuterung: str = ""          # einziger vom Modell erzeugter Text
    erzeugt_am: datetime = Field(default_factory=datetime.now)
