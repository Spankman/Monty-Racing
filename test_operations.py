import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from restore_archive import restore
from check_krok import check

class OperationsChecks(unittest.TestCase):
    def sample(self,tmp,content=b'original',expected=b'original'):
        root=Path(tmp)/'model';root.mkdir()
        manifest={'results/example.bin':hashlib.sha256(expected).hexdigest()}
        (root/'artifact_hashes.json').write_text(json.dumps(manifest))
        archive=Path(tmp)/'archive.zip'
        with ZipFile(archive,'w') as z:z.writestr('monty_v6/results/example.bin',content)
        return root,archive
    def test_restores_only_matching_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,archive=self.sample(tmp);before=(root/'artifact_hashes.json').read_bytes()
            self.assertEqual(restore(archive,root),1)
            self.assertEqual(restore(archive,root),0)
            self.assertEqual((root/'artifact_hashes.json').read_bytes(),before)
    def test_tampered_archive_is_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,archive=self.sample(tmp,b'tampered')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):restore(archive,root)
            self.assertFalse((root/'results').exists())
    def test_existing_mismatch_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,archive=self.sample(tmp);(root/'results').mkdir();p=root/'results/example.bin';p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'differs'):restore(archive,root)
            self.assertEqual(p.read_bytes(),b'changed')
    def test_missing_key_never_contacts_provider(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True),patch('check_krok.fetch') as fetch:
            with self.assertRaisesRegex(ValueError,'absent'):check('2026-11-17',Path(tmp)/'report.json')
            fetch.assert_not_called()
    def test_connection_report_contains_no_key_or_runner_records(self):
        from test_krok_adapter import KrokAdapterTests
        payload=KrokAdapterTests().fixture()
        payload['meta']['echo']='synthetic-secret'
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'KROK_API_KEY':'synthetic-secret'}),patch('check_krok.fetch',return_value=payload):
            p=Path(tmp)/'report.json';r=check('2026-11-14',p)
            self.assertNotIn('synthetic-secret',p.read_text())
            self.assertFalse(r['model_loaded']);self.assertFalse(r['predictions_generated'])
            self.assertEqual(r['accepted_runners'],2)
            self.assertNotIn('runners',r)
    def test_integrity_gate_still_rejects_missing_artifacts(self):
        from race_day import ROOT
        from monty.integrity import ArtifactError,verify_artifacts
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'artifact_hashes.json').write_text(json.dumps({'missing':hashlib.sha256(b'x').hexdigest()}))
            with self.assertRaisesRegex(ArtifactError,'Missing artifact'):verify_artifacts(root)

if __name__=='__main__':unittest.main()
