import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / "core" / "ui.py").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")

class InstitutionalUITests(unittest.TestCase):
    def test_style_and_brand(self):
        self.assertIn("dvrp-hero", UI)
        self.assertIn("OpenAlex-DVRP", UI)
    def test_navigation_anchors(self):
        for anchor in ("inicio", "protocolo", "explorador", "resultados", "bibliometria", "avanzado", "inteligencia", "proyectos"):
            self.assertIn(f'#{anchor}', UI) if anchor != "inicio" else self.assertIn('id="inicio"', UI)
            if anchor != "inicio":
                self.assertIn(f'section("{anchor}"', APP)
    def test_original_analysis_preserved(self):
        self.assertIn("buscar_publicaciones(", APP)
        self.assertIn("study_report_docx(", APP)
        self.assertIn("topic_network(df", APP)
