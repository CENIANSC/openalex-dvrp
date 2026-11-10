"""Informes 2.3; no hacen inferencias causales ni predicciones."""
import io
from xml.sax.saxutils import escape
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reports.research import register_font, LIMITATIONS

NOTE = ('Mapeo exploratorio sobre temas asignados por OpenAlex, no palabras clave de autor. '
        'Los indicadores y redes representan únicamente el conjunto descargado. '
        'Las comunidades dependen del umbral, la selección y la cobertura de metadatos. '
        'El cuadrante de baja densidad y centralidad no permite distinguir emergencia de declive. '
        'Las variaciones temáticas son descriptivas, no predicciones. ' + LIMITATIONS)


def science_docx(metrics, method, annual, topics, emerging, strategic):
    doc = Document()
    doc.add_heading('OpenAlex-DVRP 2.3 | Informe de inteligencia científica', 0)
    doc.add_paragraph('Documento automatizado para revisión académica; no sustituye un análisis metodológico del investigador.')
    doc.add_heading('Estrategia de recuperación', 1)
    for key, value in method.items():
        doc.add_paragraph(f'{key}: {value}')
    doc.add_heading('Indicadores bibliométricos', 1)
    for key, value in metrics.items():
        doc.add_paragraph(f'{key}: {value}')
    for heading, frame, limit in [('Evolución anual', annual, 30), ('Temas principales y comunidades', topics, 30),
                                   ('Variaciones temáticas recientes', emerging, 30), ('Mapa estratégico', strategic, 30)]:
        doc.add_heading(heading, 1)
        if frame.empty:
            doc.add_paragraph('No hay datos suficientes para este análisis.')
            continue
        table = doc.add_table(rows=1, cols=len(frame.columns))
        for cell, col in zip(table.rows[0].cells, frame.columns):
            cell.text = str(col)
        for row in frame.head(limit).itertuples(index=False, name=None):
            for cell, value in zip(table.add_row().cells, row):
                cell.text = str(value)
        if len(frame) > limit:
            doc.add_paragraph(f'Se muestran {limit} de {len(frame)} filas. Exporta el CSV para consultar la tabla completa.')
    doc.add_heading('Limitaciones e interpretación', 1)
    doc.add_paragraph(NOTE)
    doc.add_paragraph('Fuente: OpenAlex — https://openalex.org/ (fecha de consulta indicada en la estrategia).')
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def science_pdf(metrics, method, annual, topics, emerging, strategic):
    out = io.BytesIO()
    styles = getSampleStyleSheet()
    font = register_font()
    for style in styles.byName.values():
        style.fontName = font
    story = [Paragraph('OpenAlex-DVRP 2.3 | Informe de inteligencia científica', styles['Title']), Spacer(1, 10)]
    def section(heading, data, limit=15):
        story.append(Paragraph(escape(heading), styles['Heading2']))
        if hasattr(data, 'iterrows'):
            if data.empty:
                story.append(Paragraph('Sin datos suficientes.', styles['BodyText']))
                return
            # Columnas extensas se representan como fichas de texto para no desbordar la página.
            for _, row in data.head(limit).iterrows():
                value = ' | '.join(f'{col}: {str(row[col])[:110]}' for col in data.columns)
                story.append(Paragraph(escape(value), styles['BodyText']))
            if len(data) > limit:
                story.append(Paragraph(escape(f'Se muestran {limit} de {len(data)} registros; exporta el CSV para la tabla completa.'), styles['Italic']))
        else:
            for key, value in data.items():
                story.append(Paragraph(escape(f'{key}: {value}'), styles['BodyText']))
    section('Estrategia de recuperación', method)
    section('Indicadores bibliométricos', metrics)
    section('Evolución anual', annual)
    section('Temas principales y comunidades', topics)
    section('Variaciones temáticas recientes', emerging)
    section('Mapa estratégico', strategic)
    story.append(Paragraph('Limitaciones e interpretación', styles['Heading2']))
    story.append(Paragraph(escape(NOTE), styles['BodyText']))
    story.append(Paragraph('Fuente: OpenAlex — https://openalex.org/', styles['BodyText']))
    SimpleDocTemplate(out, pagesize=(595, 842), leftMargin=42, rightMargin=42).build(story)
    return out.getvalue()
