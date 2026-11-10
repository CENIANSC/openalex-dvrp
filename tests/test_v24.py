import unittest
import pandas as pd
from analysis.study_workflow import quality_table, selection_flow, project_bytes, read_project, study_report_docx, study_report_pdf

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([{'OpenAlex ID':'W1','Título':'Logística','Year':2024,'Cited by':3,'DOI':None}, {'OpenAlex ID':'W2','Título':'Investigación','Year':2025,'Cited by':1,'DOI':'10.1/xx'}])
        self.method = {'total_reportado_openalex':2, 'titulo_estudio':'Logística y producción'}

    def test_quality(self):
        self.assertEqual(int(quality_table(self.df).query('Campo == "DOI"')['Registros sin dato'].iloc[0]), 1)

    def test_flow(self):
        self.assertEqual(selection_flow(2,2,0,2,1).iloc[-1]['Cantidad'], 1)
        with self.assertRaises(ValueError): selection_flow(2,2,0,1,2)

    def test_roundtrip(self):
        df, method, flow = read_project(project_bytes(self.df,self.method,{'screened':1,'excluded':0}))
        self.assertEqual(len(df),2)
        self.assertEqual(method['titulo_estudio'],'Logística y producción')
        self.assertEqual(flow['screened'],1)

    def test_bad_json(self):
        with self.assertRaises(ValueError): read_project(b'{}')

    def test_reports(self):
        self.assertTrue(study_report_docx(self.df,self.method,{}).startswith(b'PK'))
        self.assertTrue(study_report_pdf(self.df,self.method,{}).startswith(b'%PDF'))

if __name__=='__main__': unittest.main()
