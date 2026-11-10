import unittest
import pandas as pd
from analysis.metrics import h_index,g_index,summarize
from analysis.networks import build_network
class TestMetrics(unittest.TestCase):
    def test_indices(self):
        v=[35,22,15,9,6,3,2,0]
        self.assertEqual(h_index(v),5)
        self.assertEqual(g_index(v),8)
    def test_empty(self):
        self.assertEqual(summarize(pd.DataFrame({"Cited by":[]}))["Índice h del conjunto"],0)
    def test_network_ids(self):
        d=pd.DataFrame({"Author IDs":["A; B","A; B"],"Authors":["Ana; Beto","Ana; Beto"]})
        self.assertEqual(build_network(d)["A"]["B"]["weight"],2)
if __name__ == "__main__":unittest.main()
