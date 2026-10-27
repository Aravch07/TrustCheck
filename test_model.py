"""Run: python -m unittest test_model -v"""
import json
import subprocess
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from ml_model import feature_rows, predict

ROOT=Path(__file__).parent


class ModelTests(unittest.TestCase):
    def test_no_future_information(self):
        reviewers=[{"id":1,"joined":datetime(2025,1,1)}]
        first={"id":1,"business_id":1,"reviewer_id":1,"posted":datetime(2026,1,1),
               "rating":3,"body":"A pleasant ordinary experience with helpful service."}
        future={**first,"id":2,"posted":first["posted"]+timedelta(hours=2),"rating":5}
        alone=feature_rows([first],reviewers)[1]
        together=feature_rows([first,future],reviewers)[1]
        self.assertEqual(alone,together)

    def test_features_and_labels_are_separate(self):
        reviewers=[{"id":1,"joined":datetime(2025,1,1)}]
        first={"id":1,"business_id":1,"reviewer_id":1,"posted":datetime(2026,1,1),
               "rating":3,"body":"Same helpful service and comfortable experience."}
        second={**first,"id":2,"posted":first["posted"]+timedelta(minutes=30),"rating":5}
        rows=feature_rows([first,second],reviewers)
        self.assertEqual(rows[2][0],1)
        self.assertEqual(rows[2][1],1)
        self.assertEqual(rows[2][2],1)
        self.assertEqual(rows[2][4],2)
        labeled=[{**first,"label":1,"score":100},{**second,"label":0,"score":0}]
        self.assertEqual(rows,feature_rows(labeled,reviewers))

    def test_business_splits_are_disjoint(self):
        report=json.loads((ROOT/"metrics.json").read_text())
        train=set(report["train_groups"])
        validation=set(report["validation_groups"])
        test=set(report["test_groups"])
        self.assertFalse(train & validation or train & test or validation & test)
        self.assertEqual(len(train|validation|test),180)

    def test_browser_matches_python(self):
        source=(ROOT/"huggingface-space/space.js").read_text()
        function=source[source.index("function predict(values)"):source.index("function showPrediction()")]
        examples=[[0,.2,0,400,.5,0],[15,.92,3,8,2,1.7],[0,0,0,0,0,0],[2,.5,1,50,1,-1]]
        script="const model="+(ROOT/"model.json").read_text()+";"+function
        script+=";console.log(JSON.stringify("+json.dumps(examples)+".map(v=>predict(v).probability)))"
        result=subprocess.run(["node","-e",script],capture_output=True,text=True,check=True)
        for row,browser in zip(examples,json.loads(result.stdout)):
            self.assertAlmostEqual(predict(row)["probability"],browser,places=12)

    def test_snapshot_has_only_seed_ids(self):
        data=json.loads((ROOT/"huggingface-space/demo_data.json").read_text())
        self.assertTrue(all(1<=r["id"]<=516 for r in data["reviews"]))
        self.assertEqual(len(data["reviews"]),516)
        self.assertNotIn("password",json.dumps(data).lower())
        self.assertFalse((ROOT/"huggingface-space/.env").exists())


if __name__=="__main__":
    unittest.main()
