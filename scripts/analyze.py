"""Read evidence bytes; run SQLite only on disposable copies. Python 3.10+."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from contextlib import closing

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def analyze(source, scratch):
    files = sorted(p for p in source.rglob('*') if p.is_file())
    before = {p.relative_to(source).as_posix(): sha(p) for p in files}
    inventory = [{'path': key, 'bytes': (source / key).stat().st_size, 'sha256': value}
                 for key, value in before.items()]
    snapshots = []
    for db in sorted(source.rglob('db.sqlite')):
        raw = db.read_bytes()
        page_size = int.from_bytes(raw[16:18], 'big')
        if page_size == 1:
            page_size = 65536
        marker = b'FORENSIC-TEST-2026-BETA'
        offsets = []
        pos = 0
        while (pos := raw.find(marker, pos)) >= 0:
            offsets.append({'offset': pos, 'page': pos // page_size + 1})
            pos += len(marker)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            copy = Path(tmp) / 'db.sqlite'
            for suffix in ('', '-wal', '-shm'):
                original = Path(str(db) + suffix)
                if original.exists():
                    shutil.copyfile(original, Path(str(copy) + suffix))
            # WAL recovery/checkpoint effects are confined to this disposable copy.
            with closing(sqlite3.connect(str(copy))) as conn:
                conn.execute('PRAGMA query_only=ON')
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                roles = {}
                count = None
                root = None
                if 'messages' in tables:
                    count = conn.execute('SELECT count(*) FROM messages').fetchone()[0]
                    roles = dict(conn.execute('SELECT role, count(*) FROM messages GROUP BY role'))
                    root = conn.execute("SELECT rootpage FROM sqlite_master WHERE name='messages'").fetchone()[0]
        pages = []
        for number in sorted({hit['page'] for hit in offsets}):
            start = (number - 1) * page_size + (100 if number == 1 else 0)
            pages.append({'page': number, 'btree_type': raw[start],
                          'cell_count': int.from_bytes(raw[start+3:start+5], 'big'),
                          'is_messages_root': number == root})
        snapshots.append({'path': db.relative_to(source).as_posix(), 'page_size': page_size,
                          'tables': tables, 'messages_count': count, 'roles': roles,
                          'messages_root_page': root, 'marker': marker.decode(),
                          'main_db_marker_hits': offsets, 'hit_page_headers': pages})
    recovered = source / 'GUI_Experiment/Analysis/recovered_messages.csv'
    with recovered.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    exported = [{'sequence': i, 'role': row['role'], 'content': row['content'],
                 'model_name': row['model_name']} for i, row in enumerate(rows, 1)]
    after = {p.relative_to(source).as_posix(): sha(p) for p in files}
    if before != after:
        raise RuntimeError('Evidence content changed during analysis')
    return {'inventory': inventory, 'snapshots': snapshots, 'messages': exported,
            'original_content_unchanged': True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = Path(os.path.abspath(args.source))
    output = Path(os.path.abspath(args.output))
    if not source.is_dir():
        parser.error('Source directory does not exist')
    if source.is_symlink() or output.is_symlink():
        parser.error('Use ordinary directories, not symbolic links')
    if output == source or source in output.parents:
        parser.error('Output must be outside the evidence directory')
    output.mkdir(parents=True, exist_ok=True)
    result = analyze(source, output)
    (output / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'files': len(result['inventory']), 'snapshots': len(result['snapshots']),
                      'original_content_unchanged': True}))

if __name__ == '__main__':
    main()
