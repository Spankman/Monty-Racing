import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from backup_zip_audit import audit_zip,verify_zip,attach_provenance

class BackupZipAuditTests(unittest.TestCase):
 def test_provenance_is_not_misrepresented_as_verified(self):
  m={'schema':'monty_source_zip_audit_v1','file_count':1}
  result=attach_provenance(m,repository='Spankman/Monty-Racing',
                           branch='development',commit_sha='a'*40)
  self.assertEqual(result['provenance']['claimed_commit_sha'],'a'*40)
  self.assertFalse(result['provenance']['commit_content_verified'])
  self.assertNotIn('provenance',m)
  with self.assertRaises(ValueError):
   attach_provenance(m,repository='repo',branch='branch',commit_sha='not-a-sha')
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
 def test_reject_multiple_roots(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('repo/a','a')
    z.writestr('other/b','b')
   with self.assertRaisesRegex(ValueError,'Multiple repository roots'):
    audit_zip(p)
 def test_reject_symlinks(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   link=zipfile.ZipInfo('repo/link')
   link.create_system=3
   link.external_attr=(0o120777 << 16)
   with zipfile.ZipFile(p,'w') as z:z.writestr(link,'../../outside')
   with self.assertRaisesRegex(ValueError,'Symlink'):
    audit_zip(p)
 def test_verify_saved_manifest_and_detect_changes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'backup.zip'
   m=Path(d)/'manifest.json'
   with zipfile.ZipFile(p,'w') as z:z.writestr('repo/a','original')
   m.write_text(json.dumps(audit_zip(p)),encoding='utf-8')
   self.assertEqual(verify_zip(p,m)['file_count'],1)
   with zipfile.ZipFile(p,'w') as z:z.writestr('repo/a','modified')
   with self.assertRaisesRegex(ValueError,'differs'):
    verify_zip(p,m)
if __name__=='__main__':unittest.main()
