import streamlit as st
import io
from datetime import datetime

from modules.address_lookup import lookup_address
from modules.alkis_wfs import get_alkis_location_data
from modules.berlin_utils import normalize_berlin_district
from modules.district_data import get_district_data
from modules.mietspiegel_wfs import get_wohnlage_from_wfs
from modules.mss_wfs import get_mss_data_from_wfs
from modules.milieuschutz_wfs import get_milieuschutz_data
from modules.bplan_wfs import get_bplan_data
from modules.hochwasser_wfs import get_hochwasser_data
from modules.denkmalschutz_wfs import get_denkmalschutz_data
from modules.fnp_wfs import get_fnp_data
from modules.bnp_manual import get_bnp_manual_info
from modules.wohnmarktreport_lookup import get_kaufkraft_data
from modules.laerm_wms import get_laerm_data
from modules.brw_wfs import get_brw_data

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER


# ── Metadata ──────────────────────────────────────────────────────────────────

META = {
    "bezirksdaten": {"source": "Lokale CSV: data/berlin_districts.csv", "date": "lokal hinterlegt"},
    "wohnlage":     {"source": "Berlin Open Data / Mietspiegel 2024 WFS", "date": "10.06.2024"},
    "mss":          {"source": "Berlin Open Data / MSS 2023 WFS", "date": "31.12.2022"},
    "milieuschutz": {"source": "Berlin Open Data / § 172 BauGB WFS", "date": "22.01.2026"},
    "bplan":        {"source": "Berlin Open Data / B-Plan WFS", "date": "03.05.2004"},
    "hochwasser":   {"source": "Berlin Open Data / Umweltatlas WFS", "date": "01.07.2018"},
    "denkmalschutz":{"source": "Berlin Open Data / Denkmale WFS", "date": "06.11.2025"},
    "fnp":          {"source": "Berlin Open Data / FNP 2025 WFS", "date": "07.02.2025"},
    "bnp":          {"source": "Berlin Open Data / Baunutzungsplan WMS", "date": "30.06.1961"},
    "kaufkraft":    {"source": "Wohnmarktreport Berlin 2026 (Berlin Hyp & CBRE)", "date": "2026"},
    "laerm":        {"source": "Berlin Open Data / Laermkarten 2022", "date": "2022"},
    "brw":          {"source": "Berlin Open Data / Bodenrichtwerte WFS", "date": "01.01.2026"},
    "adresse":      {"source": "Nominatim / OpenStreetMap", "date": "Abrufzeitpunkt"},
    "alkis":        {"source": "Berlin Open Data / ALKIS WFS", "date": "06.03.2026"},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def bool_to_text(value):
    if value is True:  return "vorhanden"
    if value is False: return "nicht vorhanden"
    return value

def safe_fetch(label, func, *args, **kwargs):
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        return None, f"{label}: {e}"

def fmt(value, unit=""):
    v = bool_to_text(value)
    if v in (None, "", "None", "none", "null"): return "-"
    return f"{v}{unit}"

def sanitize(text):
    """Ensure text is safe for ReportLab Paragraph – never empty, no raw XML chars."""
    if not isinstance(text, str):
        text = str(text) if text is not None else "-"
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.strip() or "-"


# ── HTML Components ───────────────────────────────────────────────────────────

def card_open(title, icon):
    st.html(f"""
    <div style="background:white;border-radius:12px;
        box-shadow:0 2px 16px rgba(15,36,81,0.10),0 0 0 1px rgba(15,36,81,0.05);
        margin:1.4rem 0 0 0;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#0f2451 0%,#1d4ed8 100%);
          padding:13px 20px;display:flex;align-items:center;gap:10px;">
        <span style="font-size:1.1rem">{icon}</span>
        <span style="color:white;font-family:'Segoe UI',system-ui,sans-serif;
            font-size:0.97rem;font-weight:700;letter-spacing:0.02em">{title}</span>
      </div>
      <div style="padding:14px 20px 8px 20px">
    """)

def card_close():
    st.html("</div></div>")

def value_row(label, value, source, date, unit="", error=False):
    v = fmt(value, unit)
    if error:
        val_color = "#b45309"; v = f"⚠ {v}"
    elif v == "—":
        val_color = "#9ca3af"
    else:
        val_color = "#0f172a"
    st.html(f"""
    <div style="padding:9px 0;border-bottom:1px solid #f1f5f9;
        font-family:'Segoe UI',system-ui,sans-serif;">
      <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;
          text-transform:uppercase;letter-spacing:0.07em;margin-bottom:2px">{label}</div>
      <div style="font-size:1rem;font-weight:600;color:{val_color};margin-bottom:2px">{v}</div>
      <div style="font-size:0.67rem;color:#cbd5e1;line-height:1.4">
        Quelle: {source}&nbsp;·&nbsp;Stichtag: {date}
      </div>
    </div>
    """)

def status_html(text):
    st.html(f"""
    <div style="background:#eff6ff;border-left:4px solid #2563eb;
        border-radius:0 8px 8px 0;padding:10px 16px;margin:4px 0;
        font-family:'Segoe UI',system-ui,sans-serif;
        font-size:0.88rem;font-weight:500;color:#1d4ed8;">⏳ {text}</div>
    """)

def hint_row(text, ok=False):
    if ok:
        st.html(f"""<div style="background:#f0fdf4;border-left:3px solid #22c55e;
            border-radius:0 6px 6px 0;padding:8px 12px;margin:4px 0;
            font-size:0.88rem;color:#166534;font-family:'Segoe UI',system-ui,sans-serif;">✓ {text}</div>""")
    else:
        st.html(f"""<div style="background:#fffbeb;border-left:3px solid #f59e0b;
            border-radius:0 6px 6px 0;padding:8px 12px;margin:4px 0;
            font-size:0.88rem;color:#92400e;font-family:'Segoe UI',system-ui,sans-serif;">⚠ {text}</div>""")


# ── Data Fetch ────────────────────────────────────────────────────────────────

def analyze_address(street, house_number, postal_code):
    errors = {}
    ph = st.empty()

    def step(msg):
        with ph.container():
            status_html(msg)

    step("Adresse wird aufgeloest …")
    result = lookup_address(street, house_number, postal_code)

    step("ALKIS-Daten werden geladen …")
    alkis_data, err = safe_fetch("ALKIS", get_alkis_location_data, result["latitude"], result["longitude"])
    if err:
        errors["alkis"] = err
        alkis_data = {"bezirk_wfs": None, "ortsteil_wfs": None}

    bezirk_clean   = alkis_data["bezirk_wfs"] or normalize_berlin_district(result)
    ortsteil_clean = alkis_data["ortsteil_wfs"] or result["suburb"]

    step("Bezirksdaten werden geladen …")
    district_data, err = safe_fetch("Bezirksdaten", get_district_data, bezirk_clean)
    if err:
        errors["district"] = err
        district_data = {"einwohner": None, "flaeche_km2": None, "ortsteile": None}

    step("Wohnlage wird abgerufen …")
    wohnlage_data, err = safe_fetch("Wohnlage", get_wohnlage_from_wfs, result["latitude"], result["longitude"])
    if err:
        errors["wohnlage"] = err
        wohnlage_data = {"wohnlage": None}

    step("MSS-Daten werden geladen …")
    mss_data, err = safe_fetch("MSS", get_mss_data_from_wfs, result["latitude"], result["longitude"])
    if err:
        errors["mss"] = err
        mss_data = {"status": None, "dynamik": None, "kombination": None}

    step("Milieuschutz wird geprueft …")
    milieuschutz_data, err = safe_fetch("Milieuschutz", get_milieuschutz_data, result["latitude"], result["longitude"])
    if err:
        errors["milieuschutz"] = err
        milieuschutz_data = {"in_milieuschutz": None, "gebietsname": None, "inkraft": None}

    step("B-Plan wird abgerufen …")
    bplan_data, err = safe_fetch("B-Plan", get_bplan_data, result["latitude"], result["longitude"])
    if err:
        errors["bplan"] = err
        bplan_data = {"in_bplan": None, "bezeichnung": None, "inhalt": None}

    step("Hochwasserdaten werden geladen …")
    hochwasser_data, err = safe_fetch("Hochwasser", get_hochwasser_data, result["latitude"], result["longitude"])
    if err:
        errors["hochwasser"] = err
        hochwasser_data = {"in_hochwasser": None}

    step("Denkmalschutz wird geprueft …")
    denkmalschutz_data, err = safe_fetch("Denkmalschutz", get_denkmalschutz_data, result["latitude"], result["longitude"])
    if err:
        errors["denkmalschutz"] = err
        denkmalschutz_data = {"denkmalschutz_exakt": None}

    step("FNP wird abgerufen …")
    fnp_data, err = safe_fetch("FNP", get_fnp_data, result["latitude"], result["longitude"])
    if err:
        errors["fnp"] = err
        fnp_data = {"in_fnp": None, "nutzungsart": None, "zweckbestimmung": None}

    step("Baunutzungsplan wird geladen …")
    bnp_data, err = safe_fetch("BNP", get_bnp_manual_info, result["latitude"], result["longitude"])
    if err:
        errors["bnp"] = err
        bnp_data = {"status": None}

    step("Kaufkraftdaten werden geladen …")
    kaufkraft_data, err = safe_fetch("Kaufkraft", get_kaufkraft_data, result["postcode"], bezirk_clean)
    if err:
        errors["kaufkraft"] = err
        kaufkraft_data = {"kaufkraft_plz": None, "rang_plz": None, "kaufkraft_bezirk": None,
                          "kaufkraft_berlin": None, "bezirksabweichung": False}

    step("Laermdaten werden geladen …")
    laerm_data, err = safe_fetch("Laerm", get_laerm_data, result["latitude"], result["longitude"])
    if err:
        errors["laerm"] = err
        laerm_data = {"lden": None, "lnight": None}

    step("Bodenrichtwerte werden abgerufen …")
    brw_data, err = safe_fetch("Bodenrichtwert", get_brw_data, result["latitude"], result["longitude"])
    if err:
        errors["brw"] = err
        brw_data = {"in_brw_zone": False, "grenzfall": False, "brw": None,
                    "nutzung": None, "gfz": None, "brwid": None, "zonen_details": [], "hinweis": None}

    ph.empty()

    return {
        "result": result, "alkis": alkis_data,
        "bezirk_clean": bezirk_clean, "ortsteil_clean": ortsteil_clean,
        "district_data": district_data, "wohnlage_data": wohnlage_data,
        "mss_data": mss_data, "milieuschutz_data": milieuschutz_data,
        "bplan_data": bplan_data, "hochwasser_data": hochwasser_data,
        "denkmalschutz_data": denkmalschutz_data, "fnp_data": fnp_data,
        "bnp_data": bnp_data, "kaufkraft_data": kaufkraft_data,
        "laerm_data": laerm_data, "brw_data": brw_data, "errors": errors,
    }


# ── PDF Export ────────────────────────────────────────────────────────────────

def generate_pdf(data):
    buffer = io.BytesIO()
    BLUE  = colors.HexColor("#0f2451")
    BLUE2 = colors.HexColor("#1d4ed8")
    GRAY  = colors.HexColor("#6b7280")
    DARK  = colors.HexColor("#0f172a")
    WHITE = colors.white

    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    def ps(name, **kw):
        d = dict(fontName="Helvetica", fontSize=9, textColor=DARK, spaceAfter=3, leading=13)
        d.update(kw); return ParagraphStyle(name, **d)

    title_s = ps("T",   fontSize=17, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=2)
    sub_s   = ps("S",   fontSize=8,  textColor=colors.HexColor("#bfdbfe"), spaceAfter=0)
    sec_s   = ps("Sec", fontSize=11, textColor=BLUE, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4)
    lbl_s   = ps("Lbl", fontSize=7,  textColor=GRAY, fontName="Helvetica-Bold", spaceAfter=1)
    val_s   = ps("Val", fontSize=9.5,textColor=DARK, spaceAfter=1)
    meta_s  = ps("Met", fontSize=6.5,textColor=colors.HexColor("#9ca3af"), spaceAfter=7)
    foot_s  = ps("Ft",  fontSize=7,  textColor=GRAY, alignment=TA_CENTER)
    warn_s  = ps("W",   fontSize=8.5,textColor=colors.HexColor("#92400e"))

    result = data["result"]
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    story = []

    # Header
    hdr = Table([[Paragraph(sanitize("Gutachten-Tool Berlin"), title_s),
                  Paragraph(sanitize(f"Erstellt: {now}"), sub_s)]],
                colWidths=[130*mm, 50*mm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), BLUE),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING", (0,0),(-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1),12),
    ]))
    story += [hdr, Spacer(1, 5*mm)]

    def cb(label, value, source, date, unit=""):
        v = sanitize(fmt(value, unit))
        lbl = sanitize(label.upper())
        src = sanitize(f"Quelle: {source}  ·  {date}")
        return [Paragraph(lbl, lbl_s), Paragraph(v, val_s), Paragraph(src, meta_s)]

    def two_col(left, right=None):
        if right is None: right = []
        empty_cell = lambda: [Paragraph(" ", lbl_s), Paragraph(" ", val_s), Paragraph(" ", meta_s)]
        rows = []
        for i in range(max(len(left), len(right))):
            lc = cb(*left[i])  if i < len(left)  else empty_cell()
            rc = cb(*right[i]) if i < len(right) else empty_cell()
            for j in range(3): rows.append([lc[j], rc[j]])
        t = Table(rows, colWidths=[87*mm, 87*mm])
        t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
            ("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1)]))
        return t

    def section(title):
        story.append(Paragraph(sanitize(title), sec_s))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE2, spaceAfter=3))

    r=data["result"]; bz=data["bezirk_clean"]; ot=data["ortsteil_clean"]
    dd=data["district_data"]; fn=data["fnp_data"]; bp=data["bplan_data"]
    bn=data["bnp_data"]; ms=data["milieuschutz_data"]; wl=data["wohnlage_data"]
    mss=data["mss_data"]; kk=data["kaufkraft_data"]; brw=data["brw_data"]
    hw=data["hochwasser_data"]; dk=data["denkmalschutz_data"]; lm=data["laerm_data"]

    section("Adresse & Lage")
    story.append(two_col(
        [("Adresse", r.get("standard_address_clean"), META["adresse"]["source"], META["adresse"]["date"]),
         ("Strasse / Nr.", f"{r.get('road','')} {r.get('house_number','')}", META["adresse"]["source"], META["adresse"]["date"]),
         ("PLZ", r.get("postcode"), META["adresse"]["source"], META["adresse"]["date"]),
         ("Ortsteil", ot, META["alkis"]["source"], META["alkis"]["date"]),
         ("Bezirk", bz, META["alkis"]["source"], META["alkis"]["date"])],
        [("Einwohner Bezirk", dd.get("einwohner"), META["bezirksdaten"]["source"], META["bezirksdaten"]["date"]),
         ("Flaeche Bezirk", dd.get("flaeche_km2"), META["bezirksdaten"]["source"], META["bezirksdaten"]["date"], " km2"),
         ("Ortsteile", dd.get("ortsteile"), META["bezirksdaten"]["source"], META["bezirksdaten"]["date"]),
         ("Koordinaten", f"{r.get('latitude')}, {r.get('longitude')}", META["adresse"]["source"], META["adresse"]["date"])],
    ))

    section("Planungsrecht")
    left = [("FNP", fn.get("in_fnp"), META["fnp"]["source"], META["fnp"]["date"])]
    if fn.get("in_fnp"):
        left += [("FNP Nutzung", fn.get("nutzungsart"), META["fnp"]["source"], META["fnp"]["date"]),
                 ("FNP Zweckbestimmung", fn.get("zweckbestimmung"), META["fnp"]["source"], META["fnp"]["date"])]
    left.append(("B-Plan", bp.get("in_bplan"), META["bplan"]["source"], META["bplan"]["date"]))
    if bp.get("in_bplan"):
        left += [("B-Plan Bezeichnung", bp.get("bezeichnung"), META["bplan"]["source"], META["bplan"]["date"]),
                 ("B-Plan Inhalt", bp.get("inhalt"), META["bplan"]["source"], META["bplan"]["date"])]
    right = [("Baunutzungsplan", bn.get("status"), META["bnp"]["source"], META["bnp"]["date"]),
             ("Milieuschutz", ms.get("in_milieuschutz"), META["milieuschutz"]["source"], META["milieuschutz"]["date"])]
    if ms.get("in_milieuschutz"):
        right += [("Milieuschutz Gebiet", ms.get("gebietsname"), META["milieuschutz"]["source"], META["milieuschutz"]["date"]),
                  ("Milieuschutz Inkrafttreten", ms.get("inkraft"), META["milieuschutz"]["source"], META["milieuschutz"]["date"])]
    story.append(two_col(left, right))

    section("Markt & Lage")
    story.append(two_col(
        [("Wohnlage", wl.get("wohnlage"), META["wohnlage"]["source"], META["wohnlage"]["date"]),
         ("MSS Status", mss.get("status"), META["mss"]["source"], META["mss"]["date"]),
         ("MSS Dynamik", mss.get("dynamik"), META["mss"]["source"], META["mss"]["date"]),
         ("MSS Kombination", mss.get("kombination"), META["mss"]["source"], META["mss"]["date"])],
        [("Kaufkraft PLZ", kk.get("kaufkraft_plz"), META["kaufkraft"]["source"], META["kaufkraft"]["date"]),
         ("Rang PLZ", kk.get("rang_plz"), META["kaufkraft"]["source"], META["kaufkraft"]["date"]),
         ("Kaufkraft Bezirk", kk.get("kaufkraft_bezirk"), META["kaufkraft"]["source"], META["kaufkraft"]["date"]),
         ("Berliner Durchschnitt", kk.get("kaufkraft_berlin"), META["kaufkraft"]["source"], META["kaufkraft"]["date"])],
    ))

    section("Bodenrichtwert")
    if not brw.get("in_brw_zone"):
        story.append(Paragraph("Keine Bodenrichtwertzone vorhanden.", val_s))
    elif brw.get("grenzfall"):
        story.append(Paragraph(sanitize(f"Grenzlage: {brw.get('hinweis','')}"), warn_s))
        for z in brw.get("zonen_details", []):
            story.append(Paragraph(sanitize(
                f"BRW {z.get('brw')} EUR  |  {z.get('nutzung')}  |  Bezirk: {z.get('bezirk')}  |  ID: {z.get('brwid')}"), val_s))
    else:
        story.append(two_col(
            [("Bodenrichtwert", brw.get("brw"), META["brw"]["source"], META["brw"]["date"], " EUR"),
             ("BRW Nutzung", brw.get("nutzung"), META["brw"]["source"], META["brw"]["date"])],
            [("BRW GFZ", brw.get("gfz"), META["brw"]["source"], META["brw"]["date"]),
             ("BRW-ID", brw.get("brwid"), META["brw"]["source"], META["brw"]["date"])],
        ))

    section("Umwelt & Risiken")
    story.append(two_col(
        [("Hochwasser", hw.get("in_hochwasser"), META["hochwasser"]["source"], META["hochwasser"]["date"]),
         ("Denkmalschutz", dk.get("denkmalschutz_exakt"), META["denkmalschutz"]["source"], META["denkmalschutz"]["date"])],
        [("Laerm L_DEN", lm.get("lden"), META["laerm"]["source"], META["laerm"]["date"]),
         ("Laerm L_N", lm.get("lnight"), META["laerm"]["source"], META["laerm"]["date"])],
    ))

    section("Bewertungshinweise")
    hints = []
    if brw.get("grenzfall"):     hints.append("Bodenrichtwert: Grenzlage zwischen mehreren Zonen")
    if kk.get("bezirksabweichung"): hints.append("Kaufkraft: PLZ und Bezirk stimmen nicht ueberein")
    if ms.get("in_milieuschutz"): hints.append("Milieuschutz beachten")
    if dk.get("denkmalschutz_exakt"): hints.append("Denkmalschutz vorhanden")
    for mod, err in data.get("errors", {}).items():
        hints.append(f"Datenfehler ({mod}): {err}")
    for h in hints:
        story.append(Paragraph(sanitize(f"- {h}"), warn_s))
    if not hints:
        story.append(Paragraph("Keine besonderen Hinweise.", val_s))

    addr_clean = sanitize(r.get("standard_address_clean") or "")
    story += [Spacer(1,8*mm),
              HRFlowable(width="100%", thickness=0.5, color=GRAY),
              Spacer(1,2*mm),
              Paragraph(f"Gutachten-Tool Berlin  |  {now}  |  {addr_clean}", foot_s),
              Spacer(1,2*mm),
              Paragraph("Gutachten-Tool Berlin ist eine Entwicklung von aedvice(R)", foot_s)]

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Gutachten-Tool Berlin", page_icon="🏙️", layout="wide")

st.markdown("""
<style>
* { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important; }

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: #f1f5f9 !important; }

[data-testid="stHeader"] { background: transparent !important; }

/* Hide sidebar collapse button label */
[data-testid="collapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
.st-emotion-cache-czk5ss { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] > div:first-child {
    background: #0f2451 !important;
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h3 {
    color: white !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #1e3a8a !important;
    padding-bottom: 0.5rem !important;
    margin-bottom: 1rem !important;
}
[data-testid="stSidebar"] input {
    background: #162d5e !important;
    border: 1px solid #2563eb !important;
    color: white !important;
    border-radius: 8px !important;
    caret-color: white !important;
}
[data-testid="stSidebar"] input::placeholder { color: #93c5fd !important; }

[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    padding: 0.65rem !important;
    margin-top: 0.4rem !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.45) !important;
}

/* ── TITLE ── */
h1 {
    color: #0f2451 !important;
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.4px !important;
    margin-bottom: 0 !important;
}
[data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-size: 0.88rem !important;
}

/* ── PDF download button at bottom ── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #0f2451 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.8rem 2.5rem !important;
    box-shadow: 0 4px 18px rgba(15,36,81,0.35) !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    box-shadow: 0 6px 24px rgba(15,36,81,0.45) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; border: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🗺️ Adresseingabe")
    with st.form("address_form"):
        street       = st.text_input("Straße", placeholder="z. B. Unter den Linden")
        house_number = st.text_input("Hausnummer", placeholder="z. B. 1")
        postal_code  = st.text_input("PLZ", placeholder="z. B. 10117")
        submitted    = st.form_submit_button("🔍 Prüfung starten")


# ── Header ────────────────────────────────────────────────────────────────────

st.title("🏙️ Gutachten-Tool Berlin")
st.caption("Adressbezogene Struktur-, Planungs- und Marktdaten für Berliner Gutachten")


# ── Main ──────────────────────────────────────────────────────────────────────

if submitted:
    try:
        data = analyze_address(street, house_number, postal_code)

        result             = data["result"]
        bezirk_clean       = data["bezirk_clean"]
        ortsteil_clean     = data["ortsteil_clean"]
        district_data      = data["district_data"]
        wohnlage_data      = data["wohnlage_data"]
        mss_data           = data["mss_data"]
        milieuschutz_data  = data["milieuschutz_data"]
        bplan_data         = data["bplan_data"]
        hochwasser_data    = data["hochwasser_data"]
        denkmalschutz_data = data["denkmalschutz_data"]
        fnp_data           = data["fnp_data"]
        bnp_data           = data["bnp_data"]
        kaufkraft_data     = data["kaufkraft_data"]
        laerm_data         = data["laerm_data"]
        brw_data           = data["brw_data"]
        errors             = data["errors"]

        # Generate PDF straight away – bytes must exist before st.download_button is called
        pdf_bytes = generate_pdf(data)
        fname = f"Gutachten_{result.get('postcode','')}{street.replace(' ','_')}{house_number}.pdf"

        # Status
        if errors:
            st.warning(f"Prüfung abgeschlossen – {len(errors)} Modul(e) mit Abruffehler.")
        else:
            st.success(f"✅ Prüfung erfolgreich – {result.get('standard_address_clean','')}")

        if errors:
            with st.expander(f"⚠ Fehlerdetails ({len(errors)} Module)"):
                for mod, msg in errors.items():
                    st.markdown(f"**{mod}:** `{msg}`")

        # ── Adresse & Lage ────────────────────────────────────────────────
        card_open("Adresse & Lage", "📍")
        col1, col2 = st.columns([1.2, 1])
        with col1:
            value_row("Adresse", result["standard_address_clean"], META["adresse"]["source"], META["adresse"]["date"])
            value_row("Straße / Nr.", f"{result['road']} {result['house_number']}", META["adresse"]["source"], META["adresse"]["date"])
            value_row("PLZ", result["postcode"], META["adresse"]["source"], META["adresse"]["date"])
            value_row("Ortsteil", ortsteil_clean, META["alkis"]["source"], META["alkis"]["date"])
            value_row("Bezirk", bezirk_clean, META["alkis"]["source"], META["alkis"]["date"])
            value_row("Koordinaten", f"{result['latitude']}, {result['longitude']}", META["adresse"]["source"], META["adresse"]["date"])
        with col2:
            if "district" in errors:
                value_row("Bezirksdaten", errors["district"], "", "", error=True)
            else:
                value_row("Einwohner Bezirk", district_data["einwohner"], META["bezirksdaten"]["source"], META["bezirksdaten"]["date"])
                value_row("Fläche Bezirk", district_data["flaeche_km2"], META["bezirksdaten"]["source"], META["bezirksdaten"]["date"], " km²")
                value_row("Ortsteile Bezirk", district_data["ortsteile"], META["bezirksdaten"]["source"], META["bezirksdaten"]["date"])
        card_close()

        # ── Planungsrecht ─────────────────────────────────────────────────
        card_open("Planungsrecht", "📋")
        p1, p2 = st.columns(2)
        with p1:
            if "fnp" in errors:
                value_row("FNP", errors["fnp"], "", "", error=True)
            else:
                value_row("FNP", fnp_data["in_fnp"], META["fnp"]["source"], META["fnp"]["date"])
                if fnp_data["in_fnp"]:
                    value_row("FNP Nutzung", fnp_data["nutzungsart"], META["fnp"]["source"], META["fnp"]["date"])
                    value_row("FNP Zweckbestimmung", fnp_data["zweckbestimmung"], META["fnp"]["source"], META["fnp"]["date"])
            if "bplan" in errors:
                value_row("B-Plan", errors["bplan"], "", "", error=True)
            else:
                value_row("B-Plan", bplan_data["in_bplan"], META["bplan"]["source"], META["bplan"]["date"])
                if bplan_data["in_bplan"]:
                    value_row("B-Plan Bezeichnung", bplan_data["bezeichnung"], META["bplan"]["source"], META["bplan"]["date"])
                    value_row("B-Plan Inhalt", bplan_data["inhalt"], META["bplan"]["source"], META["bplan"]["date"])
        with p2:
            if "bnp" in errors:
                value_row("Baunutzungsplan", errors["bnp"], "", "", error=True)
            else:
                value_row("Baunutzungsplan", bnp_data["status"], META["bnp"]["source"], META["bnp"]["date"])
            if "milieuschutz" in errors:
                value_row("Milieuschutz", errors["milieuschutz"], "", "", error=True)
            else:
                value_row("Milieuschutz", milieuschutz_data["in_milieuschutz"], META["milieuschutz"]["source"], META["milieuschutz"]["date"])
                if milieuschutz_data["in_milieuschutz"]:
                    value_row("Milieuschutz Gebiet", milieuschutz_data["gebietsname"], META["milieuschutz"]["source"], META["milieuschutz"]["date"])
                    value_row("Milieuschutz Inkrafttreten", milieuschutz_data["inkraft"], META["milieuschutz"]["source"], META["milieuschutz"]["date"])
        card_close()

        # ── Markt & Lage ──────────────────────────────────────────────────
        card_open("Markt & Lage", "📊")
        m1, m2 = st.columns(2)
        with m1:
            if "wohnlage" in errors:
                value_row("Wohnlage", errors["wohnlage"], "", "", error=True)
            else:
                value_row("Wohnlage", wohnlage_data["wohnlage"], META["wohnlage"]["source"], META["wohnlage"]["date"])
            if "mss" in errors:
                value_row("MSS", errors["mss"], "", "", error=True)
            else:
                value_row("MSS Status", mss_data["status"], META["mss"]["source"], META["mss"]["date"])
                value_row("MSS Dynamik", mss_data["dynamik"], META["mss"]["source"], META["mss"]["date"])
                value_row("MSS Kombination", mss_data["kombination"], META["mss"]["source"], META["mss"]["date"])
        with m2:
            if "kaufkraft" in errors:
                value_row("Kaufkraft", errors["kaufkraft"], "", "", error=True)
            else:
                value_row("Kaufkraft PLZ", kaufkraft_data["kaufkraft_plz"], META["kaufkraft"]["source"], META["kaufkraft"]["date"])
                value_row("Rang PLZ", kaufkraft_data["rang_plz"], META["kaufkraft"]["source"], META["kaufkraft"]["date"])
                value_row("Kaufkraft Bezirk", kaufkraft_data["kaufkraft_bezirk"], META["kaufkraft"]["source"], META["kaufkraft"]["date"])
                value_row("Berliner Durchschnitt", kaufkraft_data["kaufkraft_berlin"], META["kaufkraft"]["source"], META["kaufkraft"]["date"])
                if kaufkraft_data["bezirksabweichung"]:
                    st.warning("PLZ-Zuordnung und Adress-Bezirkslogik weichen voneinander ab.")
        card_close()

        # ── Bodenrichtwert ────────────────────────────────────────────────
        card_open("Bodenrichtwert", "📈")
        if "brw" in errors:
            value_row("Bodenrichtwert", errors["brw"], "", "", error=True)
        elif not brw_data["in_brw_zone"]:
            value_row("Bodenrichtwert", "nicht vorhanden", META["brw"]["source"], META["brw"]["date"])
        elif brw_data["grenzfall"]:
            st.warning(brw_data["hinweis"])
            for zone in brw_data["zonen_details"]:
                st.markdown(f"• **BRW {zone.get('brw')} €** | {zone.get('nutzung')} | Bezirk: {zone.get('bezirk')} | ID: {zone.get('brwid')}")
        else:
            b1, b2 = st.columns(2)
            with b1:
                value_row("Bodenrichtwert", brw_data["brw"], META["brw"]["source"], META["brw"]["date"], " €")
                value_row("BRW Nutzung", brw_data["nutzung"], META["brw"]["source"], META["brw"]["date"])
            with b2:
                value_row("BRW GFZ", brw_data["gfz"], META["brw"]["source"], META["brw"]["date"])
                value_row("BRW-ID", brw_data["brwid"], META["brw"]["source"], META["brw"]["date"])
        card_close()

        # ── Umwelt & Risiken ──────────────────────────────────────────────
        card_open("Umwelt & Risiken", "🌿")
        u1, u2 = st.columns(2)
        with u1:
            if "hochwasser" in errors:
                value_row("Hochwasser", errors["hochwasser"], "", "", error=True)
            else:
                value_row("Hochwasser", hochwasser_data["in_hochwasser"], META["hochwasser"]["source"], META["hochwasser"]["date"])
            if "denkmalschutz" in errors:
                value_row("Denkmalschutz", errors["denkmalschutz"], "", "", error=True)
            else:
                value_row("Denkmalschutz", denkmalschutz_data["denkmalschutz_exakt"], META["denkmalschutz"]["source"], META["denkmalschutz"]["date"])
        with u2:
            if "laerm" in errors:
                value_row("Lärm", errors["laerm"], "", "", error=True)
            else:
                value_row("Lärm L_DEN", laerm_data["lden"], META["laerm"]["source"], META["laerm"]["date"])
                value_row("Lärm L_N", laerm_data["lnight"], META["laerm"]["source"], META["laerm"]["date"])
        card_close()

        # ── Bewertungshinweise ────────────────────────────────────────────
        card_open("Bewertungshinweise", "💡")
        hints = []
        if brw_data.get("grenzfall"):
            hints.append("Bodenrichtwert kritisch: Grenzlage zwischen mehreren Zonen")
        if kaufkraft_data.get("bezirksabweichung"):
            hints.append("Kaufkraft: PLZ und Bezirk stimmen nicht überein")
        if milieuschutz_data.get("in_milieuschutz"):
            hints.append("Milieuschutz beachten")
        if denkmalschutz_data.get("denkmalschutz_exakt"):
            hints.append("Denkmalschutz vorhanden")
        if hints:
            for h in hints:
                hint_row(h, ok=False)
        else:
            hint_row("Keine besonderen Hinweise.", ok=True)
        card_close()

        # ── PDF Export – bottom of page ───────────────────────────────────
        st.html("""<div style="height:1.5rem"></div>""")
        card_open("Gutachten als PDF exportieren", "📄")
        st.download_button(
            label="⬇ PDF herunterladen",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
        )
        card_close()

    except Exception as e:
        st.error(f"Kritischer Fehler bei der Adressauflösung: {e}")

else:
    st.html("""
    <div style="background:white;border-radius:14px;
        box-shadow:0 2px 20px rgba(15,36,81,0.08);
        padding:3rem 2.5rem;text-align:center;margin-top:2rem;
        font-family:'Segoe UI',system-ui,sans-serif;">
      <div style="font-size:3rem;margin-bottom:1rem">🏙️</div>
      <div style="font-size:1.3rem;font-weight:800;color:#0f2451;margin-bottom:0.5rem">
        Gutachten-Tool Berlin
      </div>
      <div style="font-size:0.92rem;color:#64748b;max-width:360px;margin:0 auto;line-height:1.6">
        Adresse links eingeben und <strong>Prüfung starten</strong> klicken,
        um adressbezogene Markt- und Planungsdaten abzurufen.
      </div>
    </div>
    """)