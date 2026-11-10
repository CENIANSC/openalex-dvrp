"""Informes académicos descriptivos con texto Unicode en PDF."""
import io
import os
from xml.sax.saxutils import escape
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

LIMITATIONS = ('Resultados descriptivos del subconjunto descargado, no necesariamente del universo OpenAlex. '
               'La cobertura, las citas y la clasificación temática cambian con el tiempo. '
               'Las citas acumuladas favorecen publicaciones antiguas; no se calculan citas normalizadas por campo. '
               'La selección de documentos y la interpretación requieren revisión del investigador.')


def register_font():
    if 'DVRPUnicode' in pdfmetrics.getRegisteredFontNames():
        return 'DVRPUnicode'
    candidates = [os.path.join(os.path.dirname(__file__), '..', 'assets', 'DejaVuSans.ttf'),
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for path in candidates:
        if os.path.isfile(path):
            pdfmetrics.registerFont(TTFont('DVRPUnicode', path))
            return 'DVRPUnicode'
    return 'Helvetica'


def research_docx(metrics, method, annual, comparison=None):
    doc = Document()
    doc.add_heading('OpenAlex-DVRP 2.2 | Informe de investigación bibliométrica', 0)
    doc.add_paragraph('Informe descriptivo generado automáticamente; requiere revisión científica.')
    doc.add_heading('Fuente y estrategia de recuperación', 1)
    for k, v in method.items():
        doc.add_paragraph(f'{k}: {v}')
    doc.add_heading('Indicadores del conjunto', 1)
    for k, v in metrics.items():
        doc.add_paragraph(f'{k}: {v}')
    doc.add_heading('Evolución anual', 1)
    table = doc.add_table(rows=1, cols=3)
    for cell, title in zip(table.rows[0].cells, ['Año', 'Publicaciones', 'Citas']): cell.text = title
    for _, row in annual.iterrows():
        for cell, value in zip(table.add_row().cells, [int(row['Año']), int(row['Publicaciones']), int(row['Citas'])]): cell.text = str(value)
    if comparison is not None and not comparison.empty:
        doc.add_heading('Comparación descriptiva', 1)
        for _, row in comparison.iterrows(): doc.add_paragraph(' | '.join(f'{col}: {row[col]}' for col in comparison.columns))
    doc.add_heading('Limitaciones metodológicas', 1)
    doc.add_paragraph(LIMITATIONS)
    doc.add_heading('Fuente de datos', 1)
    doc.add_paragraph('OpenAlex. https://openalex.org/ — API: https://docs.openalex.org/')
    output = io.BytesIO(); doc.save(output); return output.getvalue()


def research_pdf(metrics, method, annual, comparison=None):
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    font = register_font()
    for style in styles.byName.values():
        style.fontName = font
    story = [Paragraph('OpenAlex-DVRP 2.2 | Informe bibliométrico', styles['Title']), Spacer(1, 12),
             Paragraph('Estrategia de recuperación', styles['Heading2'])]
    for k, v in method.items(): story.append(Paragraph(escape(f'{k}: {v}'), styles['BodyText']))
    story.extend([Spacer(1, 10), Paragraph('Indicadores', styles['Heading2'])])
    for k, v in metrics.items(): story.append(Paragraph(escape(f'{k}: {v}'), styles['BodyText']))
    story.append(Paragraph('Producción anual', styles['Heading2']))
    rows = [['Año', 'Publicaciones', 'Citas']] + [[str(int(r['Año'])), str(int(r['Publicaciones'])), str(int(r['Citas']))] for _, r in annual.iterrows()]
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID',(0,0),(-1,-1),.4,colors.grey)]))
    story.append(t)
    if comparison is not None and not comparison.empty:
        story.append(Paragraph('Comparación descriptiva', styles['Heading2']))
        for _, row in comparison.iterrows():
            story.append(Paragraph(escape(' | '.join(f'{col}: {row[col]}' for col in comparison.columns)), styles['BodyText']))
    story.extend([Spacer(1, 10), Paragraph('Limitaciones metodológicas', styles['Heading2']),
                  Paragraph(escape(LIMITATIONS), styles['BodyText']),
                  Paragraph('Fuente: OpenAlex (https://openalex.org/)', styles['BodyText'])])
    SimpleDocTemplate(output, pagesize=(595,842), leftMargin=42, rightMargin=42).build(story)
    return output.getvalue()
