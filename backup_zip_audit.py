"""Offline verification for downloaded GitHub source ZIP backups.

A GitHub source ZIP is a snapshot, not a full Git mirror. This tool checks
archive integrity, unsafe names, duplicate entries and generates a reproducible
SHA-256 manifest. Keep the manifest outside GitHub alongside the ZIP.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import PurePosixPath

def audit_zip(path):
    files={}
    root=None
    with zipfile.ZipFile(path) as archive:
        bad=archive.testzip()
        if bad is not None:
            raise ValueError('Corrupt archive entry: '+bad)
        for entry in archive.infolist():
            name=entry.filename
            parts=PurePosixPath(name).parts
            if not parts or name.startswith('/') or '..' in parts or '\\' in name:
                raise ValueError('Unsafe archive path: '+name)
            if root is None:
                root=parts[0]
            elif parts[0]!=root:
                raise ValueError('Multiple repository roots in archive')
            # Unix symlinks can point outside the extracted repository.
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink entry not permitted: '+name)
            if entry.is_dir():
                continue
            relative='/'.join(parts[1:])
            if not relative:
                raise ValueError('Missing source root directory')
            if relative in files:
                raise ValueError('Duplicate file: '+relative)
            data=archive.read(entry)
            files[relative]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    if not files:
        raise ValueError('Archive contains no files')
    return {'schema':'monty_source_zip_audit_v1','kind':'SOURCE_SNAPSHOT_NOT_GIT_HISTORY',
            'file_count':len(files),'files':dict(sorted(files.items()))}

def verify_zip(path, manifest_path):
    """Compare a backup against a previously saved independent manifest."""
    with open(manifest_path,encoding='utf-8') as source:
        expected=json.load(source)
    actual=audit_zip(path)
    if expected.get('schema')!=actual['schema'] or expected.get('kind')!=actual['kind']:
        raise ValueError('Unsupported backup manifest')
    if expected.get('file_count')!=actual['file_count'] or expected.get('files')!=actual['files']:
        raise ValueError('Backup differs from saved manifest')
    return actual

def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if len(argv)==3 and argv[0]=='--verify':
        result=verify_zip(argv[1],argv[2])
        print('MATCH:',result['file_count'],'files match saved manifest')
        return
    if len(argv)!=2:
        raise SystemExit('Usage: python backup_zip_audit.py backup.zip manifest.json OR --verify backup.zip manifest.json')
    result=audit_zip(argv[0])
    with open(argv[1],'x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,sort_keys=True)
        out.write('\n')
    print('Verified',result['file_count'],'files; source snapshot only')

if __name__=='__main__':
    main()
