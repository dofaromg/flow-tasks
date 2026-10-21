import json, tempfile, unittest
from pathlib import Path
import numpy as np
from mrliou_800ai.trace import TraceChain
from mrliou_800ai.datastore import ReversibleStore
from mrliou_800ai.physics.conservation import mass_terms

class RuntimeTests(unittest.TestCase):
    def test_mass_constant_field(self):
        t=np.linspace(0,1,4); rho=np.ones((4,5,6)); u=np.zeros_like(rho); v=np.zeros_like(rho)
        r=mass_terms(rho,u,v,t,1.0,1.0)
        self.assertLess(r["abs_max"], 1e-12)
    def test_reversible_write(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); tr=TraceChain(root/"logs"); store=ReversibleStore(root,tr)
            store.write_text("data/a.txt","one"); second=store.write_text("data/a.txt","two")
            self.assertTrue(Path(second["snapshot"]).exists())

if __name__ == "__main__": unittest.main()
