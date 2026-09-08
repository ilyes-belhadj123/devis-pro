from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CORAIL = colors.HexColor("#FF6A3D")
CHARCOAL = colors.HexColor("#1A1712")
BORDER = colors.HexColor("#E5DFD6")

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _date_francaise(dt: datetime) -> str:
    return f"{dt.day:02d} {MOIS_FR[dt.month - 1]} {dt.year}"


def construire_pdf_devis(compte_nom: str, categorie: str, formule: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Devis SnapDevis Entretien",
    )

    style_titre = ParagraphStyle("titre", fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=CORAIL)
    style_meta = ParagraphStyle("meta", fontName="Helvetica", fontSize=9.5, leading=13, textColor=CHARCOAL, spaceBefore=4)
    style_total_label = ParagraphStyle(
        "total_label", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=CHARCOAL, alignment=TA_RIGHT
    )
    style_total_montant = ParagraphStyle(
        "total_montant", fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=CORAIL, alignment=TA_RIGHT
    )
    style_footer = ParagraphStyle("footer", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#726A5C"))

    elements: list = []
    elements.append(Paragraph("Snap·Devis Entretien", style_titre))
    elements.append(Paragraph(compte_nom, style_meta))
    elements.append(Paragraph(f"Devis généré le {_date_francaise(datetime.now())} — formule {formule['label']} ({categorie})", style_meta))
    elements.append(Spacer(1, 0.7 * cm))

    entetes = ["Désignation", "Catégorie", "Qté", "Prix unit.", "Sous-total"]
    donnees = [entetes]
    for ligne in formule["lignes"]:
        donnees.append(
            [
                ligne["designation"],
                ligne["categorie"],
                f"{ligne['quantite']:g} {ligne['unite']}",
                f"{ligne['prix_unitaire']:.2f} €",
                f"{ligne['sous_total']:.2f} €",
            ]
        )

    table = Table(donnees, colWidths=[6.3 * cm, 2.8 * cm, 3.1 * cm, 2.6 * cm, 2.6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), CHARCOAL),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, CHARCOAL),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 1), (-1, -1), CHARCOAL),
                ("LINEBELOW", (0, 1), (-1, -1), 0.6, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.9 * cm))

    total_table = Table(
        [[Paragraph("Total estimé", style_total_label), Paragraph(f"{formule['total']:.2f} €", style_total_montant)]],
        colWidths=[13.8 * cm, 3.6 * cm],
    )
    total_table.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.3, CHARCOAL), ("TOPPADDING", (0, 0), (-1, -1), 10)]))
    elements.append(total_table)
    elements.append(Spacer(1, 2 * cm))
    elements.append(Paragraph("SnapDevis Entretien — prototype de démonstration", style_footer))

    doc.build(elements)
    return buffer.getvalue()
