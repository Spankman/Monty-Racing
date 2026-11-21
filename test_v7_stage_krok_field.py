import json
import tempfile
import unittest
from pathlib import Path
from v7.stage_krok_field import stage

class StageKrokV7Tests(unittest.TestCase):
    def test_stages_unverified_field(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"snapshot.json"
            src.write_text(json.dumps({"runners":[
                {"meeting":"Whanganui","race":"3","number":str(i),"horse":"TEST "+str(i),
                 "odds":i+2,"betting_authorised":False} for i in range(1,5)]}))
            result=stage(src,"Whanganui","3",root/"field.csv")
            self.assertFalse(result["betting_authorised"])
            self.assertIn("UNVERIFIED",result["status"])
            self.assertTrue((root/"field.csv").exists())
            with self.assertRaises(FileExistsError):
                stage(src,"Whanganui","3",root/"field.csv")
    def test_rejects_blank_horse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"snapshot.json"
            src.write_text(json.dumps({"runners":[
                {"meeting":"Whanganui","race":"3","number":str(i),"horse":" ",
                 "odds":i+2,"betting_authorised":False} for i in range(1,5)]}))
            with self.assertRaisesRegex(ValueError,"Blank runner"):
                stage(src,"Whanganui","3",root/"field.csv")
    def test_rejects_unauthorised_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"snapshot.json"
            src.write_text(json.dumps({"runners":[
                {"meeting":"Whanganui","race":"3","number":"1","horse":"TEST",
                 "odds":3,"betting_authorised":True} for _ in range(3)]}))
            with self.assertRaises(ValueError):
                stage(src,"Whanganui","3",root/"field.csv")
if __name__=="__main__":
    unittest.main()
