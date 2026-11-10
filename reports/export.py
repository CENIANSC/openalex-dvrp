"""Informes descriptivos: no sustituyen una revisión crítica académica."""
import io
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from xml.sax.saxutils import escape

def create_docx(metrics, method, yearly):
    doc=Document();doc.add_heading("OpenAlex-DVRP 2.1 | Informe bibliométrico",0)
    doc.add_heading("Metodología de recuperación",1)
    for k,v in method.items(): doc.add_paragraph(f"{k}: {v}")
    doc.add_heading("Indicadores del conjunto descargado",1)
    for k,v in metrics.items(): doc.add_paragraph(f"{k}: {v}")
    doc.add_heading("Producción por año",1)
    t=doc.add_table(rows=1, cols=3);t.style="Light Shading Accent 1"
    for c,s in zip(t.rows[0].cells,["Año","Publicaciones","Citas"]):c.text=s
    for _,r in yearly.iterrows():
        cells=t.add_row().cells
        for c,s in zip(cells,[int(r["Año"]),int(r["Publicaciones"]),int(r["Citas"])]):c.text=str(s)
    doc.add_heading("Limitaciones",1)
    doc.add_paragraph("Los indicadores representan únicamente los registros descargados. La cobertura y las citas de OpenAlex pueden variar con el tiempo. El índice h y el índice g corresponden al conjunto recuperado, no a cada autor.")
    out=io.BytesIO();doc.save(out);return out.getvalue()

def create_pdf(metrics,method,yearly):
    out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=(595,842),rightMargin=40,leftMargin=40)
    styles=getSampleStyleSheet();story=[Paragraph("OpenAlex-DVRP 2.1 - Informe bibliometrico",styles["Title"]),Spacer(1,15),Paragraph("Metodologia",styles["Heading2"])]
    for k,v in method.items():story.append(Paragraph(escape(f"{k}: {v}"),styles["BodyText"]))
    story.extend([Spacer(1,12),Paragraph("Indicadores del conjunto descargado",styles["Heading2"])])
    for k,v in metrics.items():story.append(Paragraph(escape(f"{k}: {v}"),styles["BodyText"]))
    story.extend([Spacer(1,12),Paragraph("Produccion anual",styles["Heading2"])])
    rows=[["Anio","Publicaciones","Citas"]]+[[str(int(r["Año"])),str(int(r["Publicaciones"])),str(int(r["Citas"]))] for _,r in yearly.iterrows()]
    table=Table(rows,repeatRows=1);table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("GRID",(0,0),(-1,-1),.4,colors.grey),("BOTTOMPADDING",(0,0),(-1,-1),6)]));story.append(table)
    story.extend([Spacer(1,12),Paragraph("Limitaciones",styles["Heading2"]),Paragraph("Los indicadores corresponden a los registros descargados y pueden cambiar con la cobertura de OpenAlex. Los indices h y g se refieren al conjunto, no a los autores.",styles["BodyText"])])
    doc.build(story);return out.getvalue()
