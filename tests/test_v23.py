import unittest
import pandas as pd
from analysis.science_mapping import (topic_network, topic_table, thematic_evolution,
    emerging_topics, strategic_map, reference_network, edge_table)
from reports.science_report import science_docx, science_pdf

class MappingTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {'OpenAlex ID':'https://openalex.org/W1', 'Year':2020, 'Themes':'A; B', 'Referenced works':'R1; R2; https://openalex.org/W2', 'Cited by':4},
            {'OpenAlex ID':'https://openalex.org/W2', 'Year':2022, 'Themes':'A; C', 'Referenced works':'R1; R2', 'Cited by':3},
            {'OpenAlex ID':'https://openalex.org/W3', 'Year':2024, 'Themes':'B; C', 'Referenced works':'R2; R3', 'Cited by':2},
            {'OpenAlex ID':'https://openalex.org/W4', 'Year':2025, 'Themes':'A; C', 'Referenced works':'R1; R3', 'Cited by':1},
        ])
    def test_topic_map(self):
        graph = topic_network(self.df, min_occurrences=2)
        self.assertEqual(graph.number_of_nodes(), 3)
        self.assertEqual(graph['A']['C']['weight'], 2)
        self.assertEqual(len(topic_table(graph)), 3)
    def test_evolution(self):
        self.assertFalse(thematic_evolution(self.df).empty)
        self.assertFalse(emerging_topics(self.df, min_total=1).empty)
    def test_strategic(self):
        self.assertFalse(strategic_map(topic_network(self.df, min_occurrences=1)).empty)
    def test_references(self):
        self.assertEqual(reference_network(self.df, 'coupling', min_shared=2).number_of_edges(), 1)
        self.assertTrue(reference_network(self.df, 'citation').has_edge('https://openalex.org/W1','https://openalex.org/W2'))
        self.assertTrue(reference_network(self.df, 'cocitation', min_shared=1).number_of_edges() > 0)
        self.assertIn('Peso', edge_table(reference_network(self.df)).columns)
    def test_reports(self):
        from analysis.metrics import yearly
        annual = yearly(self.df)
        topics = topic_table(topic_network(self.df))
        trends = emerging_topics(self.df, min_total=1)
        strategy = strategic_map(topic_network(self.df))
        self.assertTrue(science_docx({'Publicaciones':4},{'terminos':'Logística'},annual,topics,trends,strategy).startswith(b'PK'))
        self.assertTrue(science_pdf({'Publicaciones':4},{'terminos':'Logística'},annual,topics,trends,strategy).startswith(b'%PDF'))

if __name__ == '__main__': unittest.main()
