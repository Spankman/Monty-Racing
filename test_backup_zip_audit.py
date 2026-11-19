import tempfile
import unittest
import zipfile
from pathlib import Path
from backup_zip_audit import audit_zip

class BackupZipAuditTests(unittest.TestCase):
 def test_valid_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('repo/main.py','print(1)')
   result=audit_zip(p)
   self.assertEqual(result['file_count'],1)
   self.assertIn('main.py',result['files'])
   self.assertEqual(result['kind'],'SOURCE_SNAPSHOT_NOT_GIT_HISTORY')
 def test_reject_traversal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('repo/../bad','bad')
   with self.assertRaises(ValueError):audit_zip(p)
 def test_reject_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('repo/a','a')
    z.writestr('repo/a','b')
   with self.assertRaises(ValueError):audit_zip(p)
if __name__=='__main__':unittest.main()
