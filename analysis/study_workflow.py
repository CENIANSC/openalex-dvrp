"""Reproducibilidad y control metodológico: no realiza selección automática de elegibilidad."""
import io
import json
from datetime import datetime, timezone
from xml.sax.saxutils import escape
import pandas as pd
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reports.research import register_font
from analysis.metrics import summarize

MAX_PROJECT_BYTES = 25 * 1024 * 1024


def quality_table(df):
    n = len(df)
    rows = []
    for col in ('OpenAlex ID', 'Título', 'Year', 'Authors', 'Institutions', 'DOI', 'Abstract', 'Referenced works', 'Cited by'):
        if col not in df:
            missing = n
        else:
            values = df[col]
            missing = int((values.isna() | values.astype(str).str.strip().isin(['', 'None', 'nan'])).sum())
        rows.append({'Campo': col, 'Registros sin dato': missing, 'Cobertura (%)': round(100*(n-missing)/n, 2) if n else 0})
    duplicate = int(df['OpenAlex ID'].dropna().duplicated().sum()) if 'OpenAlex ID' in df else 0
    rows.append({'Campo': 'ID duplicado', 'Registros sin dato': duplicate, 'Cobertura (%)': None})
    return pd.DataFrame(rows)


def selection_flow(identified, downloaded, duplicates, screened, excluded):
    if not (0 <= duplicates <= downloaded <= identified and 0 <= excluded <= screened <= downloaded-duplicates):
        raise ValueError('Las cantidades del flujo no son consistentes')
    return pd.DataFrame([
        {'Etapa': 'Resultados identificados por OpenAlex', 'Cantidad': identified},
        {'Etapa': 'Registros descargados', 'Cantidad': downloaded},
        {'Etapa': 'Duplicados detectados', 'Cantidad': duplicates},
        {'Etapa': 'Registros examinados manualmente', 'Cantidad': screened},
        {'Etapa': 'Excluidos tras cribado manual', 'Cantidad': excluded},
        {'Etapa': 'Incluidos tras cribado manual', 'Cantidad': screened-excluded},
    ])


def project_bytes(df, method, flow):
    data = {'schema': 'openalex-dvrp-project-2.4', 'saved_utc': datetime.now(timezone.utc).isoformat(),
            'method': method, 'selection': flow, 'columns': list(df.columns),
            'records': json.loads(df.to_json(orient='records', date_format='iso', force_ascii=False))}
    payload = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
    if len(payload) > MAX_PROJECT_BYTES:
        raise ValueError('El proyecto supera 25 MB; exporta los registros CSV por separado.')
    return payload


def read_project(payload):
    if len(payload) > MAX_PROJECT_BYTES:
        raise ValueError('Archivo demasiado grande (máximo 25 MB)')
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError('JSON inválido') from exc
    if not isinstance(data, dict) or data.get('schema') != 'openalex-dvrp-project-2.4':
        raise ValueError('Formato de proyecto no compatible')
    if not isinstance(data.get('records'), list) or not isinstance(data.get('method'), dict) or not isinstance(data.get('selection'), dict):
        raise ValueError('Estructura del proyecto incompleta')
    if len(data['records']) > 50000:
        raise ValueError('El proyecto supera el límite de registros')
    df = pd.DataFrame(data['records'], columns=data.get('columns'))
    if 'OpenAlex ID' not in df.columns:
        raise ValueError('Falta la columna OpenAlex ID')
    return df, data['method'], data['selection']


def report_sections(df, method, flow):
    metrics = summarize(df)
    identified = max(len(df), int(method.get('total_reportado_openalex') or len(df)))
    duplicates = int(df['OpenAlex ID'].dropna().duplicated().sum()) if 'OpenAlex ID' in df else 0
    screened = min(max(0, int(flow.get('screened', 0))), max(0, len(df)-duplicates))
    excluded = min(max(0, int(flow.get('excluded', 0))), screened)
    sections = [
        ('Título', str(method.get('titulo_estudio') or 'Estudio bibliométrico exploratorio')),
        ('Pregunta de investigación', str(method.get('pregunta_investigacion') or 'Pendiente de definir por el investigador.')),
        ('Objetivo', str(method.get('objetivo_estudio') or 'Pendiente de definir por el investigador.')),
        ('Metodología', f"Fuente: OpenAlex API. Fecha UTC: {method.get('fecha_consulta_utc', 'no registrada')}. Filtros: {method.get('filtros', 'no registrados')}. Criterios de inclusión: {method.get('criterios_inclusion', 'no especificados')}. Criterios de exclusión: {method.get('criterios_exclusion', 'no especificados')}."),
        ('Selección de documentos', f'Resultados reportados: {identified}; descargados: {len(df)}; duplicados: {duplicates}; examinados manualmente: {screened}; excluidos manualmente: {excluded}; incluidos tras cribado: {screened-excluded}. Los registros no examinados no se consideran incluidos.'),
        ('Resultados descriptivos', '; '.join(f'{key}: {value}' for key, value in metrics.items())),
        ('Discusión', 'Pendiente de interpretación crítica y contraste con literatura pertinente por el investigador.'),
        ('Limitaciones', 'Análisis basado en el subconjunto descargado. Cobertura, citas y clasificaciones de OpenAlex pueden variar. El cribado manual debe documentarse; no se ha realizado una evaluación de riesgo de sesgo ni una revisión sistemática completa.'),
        ('Fuente de datos', 'OpenAlex: https://openalex.org/'),
    ]
    return sections


def study_report_docx(df, method, flow):
    doc = Document()
    doc.add_heading('OpenAlex-DVRP 2.4 | Borrador académico', 0)
    for heading, content in report_sections(df, method, flow):
        doc.add_heading(heading, level=1)
        doc.add_paragraph(content)
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()


def study_report_pdf(df, method, flow):
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    font = register_font()
    for style in styles.byName.values():
        style.fontName = font
    story = [Paragraph('OpenAlex-DVRP 2.4 | Borrador académico', styles['Title']), Spacer(1, 14)]
    for heading, content in report_sections(df, method, flow):
        story.extend([Paragraph(escape(heading), styles['Heading2']), Paragraph(escape(content), styles['BodyText']), Spacer(1, 9)])
    SimpleDocTemplate(output, pagesize=(595, 842), leftMargin=42, rightMargin=42).build(story)
    return output.getvalue()
