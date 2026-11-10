import unittest
import pandas as pd
from analysis.comparative import compare_periods, compare_entities, international_collaboration
from analysis.reproducibility import manifest_bytes
from reports.research import research_pdf, research_docx

class V22Tests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([{'OpenAlex ID':'W1','Year':2020,'Cited by':4,'Countries':'MX; US','Institutions':'A; B','Authors':'Ana; Bob','Journal':'J'}, {'OpenAlex ID':'W2','Year':2022,'Cited by':2,'Countries':'MX','Institutions':'A','Authors':'Ana','Journal':'K'}])
    def test_comparison(self):
        result = compare_periods(self.df, 2020, 2021, 2022, 2023)
        self.assertEqual(result['Publicaciones'].tolist(), [1, 1])
        self.assertEqual(international_collaboration(self.df), 1)
        self.assertEqual(compare_entities(self.df,'Institutions').iloc[0]['Publicaciones'],2)
    def test_exports(self):
        from analysis.metrics import yearly
        annual = yearly(self.df)
        self.assertTrue(research_pdf({'Publicaciones':2},{'terminos':'Logística'},annual).startswith(b'%PDF'))
        self.assertTrue(research_docx({'Publicaciones':2},{'terminos':'Logística'},annual).startswith(b'PK'))
        self.assertIn('identificadores_sha256', manifest_bytes({'terminos':'test'},self.df).decode())

if __name__ == '__main__': unittest.main()
