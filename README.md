# 온프레미스 AI 포렌식 예비 실험

**로컬 AI와의 대화는 어디에 기록되며, 대화를 삭제하면 그 흔적도 사라지는가?**

Ollama와 Qwen2.5를 이용한 단일 Windows 환경에서 CLI 입력 이력, GUI 대화 저장, 삭제 후 문자열 잔존을 확인한 예비 실습입니다. 실험 자료를 사본에서 다시 분석한 결과, GUI 대화 삭제 후 `messages` SQL 조회는 0건이었지만 main DB에는 실험용 식별 문자열이 3곳에 남아 있었습니다.

## 1. 실험 목적

사용자의 입력과 AI 응답을 분석하기에 앞서, 실행 방식에 따라 어떤 기록이 생성되고 삭제 후에도 무엇이 남는지 살펴보고자 했습니다. 이번 실습은 아티팩트의 생성·저장·잔존 여부를 확인하는 첫 단계이며, 행위 주체의 확정이나 대화 전체 복원을 목표로 한 실험은 아닙니다.

## 2. 실험 환경과 식별 문자열

| 항목 | 수집 자료에서 확인한 값 |
|---|---|
| 실행 환경 | Windows, 세부 수집값은 아래 한계 참조 |
| Ollama | 버전 기록 `0.40.2` |
| 모델 | `qwen2.5:0.5b` |
| CLI 실행 중 기록 | CPU 100%, context 4096 |
| CLI 식별 문자열 | `FORENSIC-TEST-2026-ALPHA` |
| GUI 식별 문자열 | `FORENSIC-TEST-2026-BETA` |
| GUI 저장 자료 | `db.sqlite`·`db.sqlite-wal`·`db.sqlite-shm` |

식별 문자열은 실습 대화를 다른 데이터와 구분하기 위해 사용했습니다. CLI와 GUI에는 서로 다른 문자열을 사용했습니다. GUI 제품명·버전은 현재 자료만으로 확정하지 않았습니다.

## 3. 진행 과정

다음은 수집 폴더와 파일 내용, 실험자가 설명한 삭제 동작을 바탕으로 정리한 단계입니다. 정확한 명령 순서 전체가 보존된 실행 로그는 아닙니다.

1. **기준 자료 수집:** `Evidence/Before`, `Installed`, `PreRun` 등에 시스템·프로세스·모델·파일 목록을 수집했습니다.
2. **CLI 대화 실행:** 모델 설명 질문, ALPHA 문자열 기억 요청, 문자열 재질문을 입력했습니다. `Analysis/history_copy.txt`에서 질문 3개와 `/bye`를 확인했습니다.
3. **GUI 대화 실행:** 모델 확인 질문, BETA 문자열 기억 요청, 문자열 재질문을 입력했습니다. 저장된 대화 CSV에는 사용자 질문 3건과 assistant 응답 3건이 있습니다.
4. **GUI 전후 사본 수집:** `GUI_Experiment/Before`와 `After`의 DB·WAL·SHM을 비교했습니다. SQL 논리 상태는 각각 `messages` 0건과 6건이었습니다.
5. **대화 삭제 전후 비교:** 실험자가 GUI에서 대화를 삭제한 뒤 수집한 `Deletion_Experiment/AfterDeletion`에서는 SQL 조회가 0건이었습니다. 삭제 전 사본은 6건이었습니다.
6. **잔존 흔적 분석:** 삭제 후 main DB의 바이트를 검색해 BETA 문자열의 위치를 구하고, 해당 페이지와 `messages` 테이블의 관계를 확인했습니다.

공유 자료 정리 시에는 원본 54개 파일의 SHA-256을 복사 전후 비교했습니다. SQLite 조회는 DB·WAL·SHM을 함께 복사한 임시 사본에서만 실행했습니다.

## 4. 확인한 결과와 근거

| 질문 | 확인한 결과 | 근거 |
|---|---|---|
| CLI에서 무엇을 확인했는가? | 질문 3개, ALPHA 식별 문자열, `/bye` | 원본 history 사본을 읽어 확인; 원본은 공유 제외 |
| GUI 대화가 저장되었는가? | SQL 조회 6건: user 3건, assistant 3건 | [검증 집계](#verified-results), [실험 대화 기록](#conversation) |
| 삭제 후 SQL로 대화를 조회할 수 있었는가? | `messages` 0건 | 삭제 후 사본의 SQL 조회 |
| 삭제 후 문자열도 모두 사라졌는가? | BETA 문자열 3곳 잔존 | main DB 바이트 검색 |
| 잔존 위치는 어디인가? | 5번 페이지, 오프셋 18915·19416·19686 | 페이지 크기 4096; 오프셋은 파일 시작에서 0 기준 |
| 그 페이지의 현재 상태는 무엇인가? | `messages` 루트 페이지, 테이블 leaf 타입 `0x0D`, 유효 셀 0개 | SQLite 스키마 및 페이지 헤더 |

대화 사본의 본문은 기존 `recovered_messages.csv`에서 가져왔습니다. SQL로 role별 건수는 재검증했지만, 각 본문을 SQL에서 다시 추출해 CSV와 대조한 것은 아닙니다.

## 5. 결과의 의미와 한계

이번 사본에서는 **논리적으로 조회되지 않는 대화의 식별 문자열이 파일 바이트에 남을 수 있음**을 확인했습니다. 따라서 대화 삭제 여부를 살펴볼 때 SQL 조회와 파일 수준 분석을 함께 검토할 필요가 있음을 보여줍니다.

- 문자열 3곳은 대화 3개나 완전한 레코드 3개의 복원을 뜻하지 않습니다. 대화 전체를 복구했다고 주장하지 않습니다.
- 삭제 전 4KB main DB의 논리 상태는 WAL을 함께 처리해야 확인됩니다. main DB에서 문자열이 발견되지 않았다는 사실만으로 해당 대화가 없었다고 판단할 수 없습니다.
- 단일 환경의 예비 실험입니다. GUI 삭제 동작과 파일 수집 사이의 정확한 시간·종료 순서, SQLite 설정을 모두 통제한 반복 실험은 아닙니다.
- OS 수집값은 `Windows 10 Home / 2009 / build 26200`입니다. 이 값만으로 실제 제품 버전을 확정하지 않았습니다.
- SHA-256 일치는 이번 복사·분석 과정의 파일 내용 보존을 확인합니다. 최초 수집 당시의 전체 증거 관리 절차나 OS 메타데이터까지 증명하지 않습니다.
- 앱의 `role` 값은 저장된 분류이며, 실제 행위 주체나 수사상 증거능력을 확정하는 근거로 사용하지 않습니다.

## 6. 자료와 분석 코드

| 파일 | 내용 |
|---|---|
| [docs/CONVERSATION.md](#conversation) | 실험 질문·응답을 순서대로 읽는 열람용 문서 |
| [docs/METHODS.md](#methods) | 분석 절차, SQL, 페이지 계산 방식, 검증 범위 |
| [scripts/analyze.py](#analysis-code) | 임시 사본의 SQL 조회, main DB 식별 문자열 검색, SHA-256 비교 |
| [data/verified_summary.json](#verified-results) | 스냅샷별 집계와 바이트 위치 |
| [data/messages_sanitized.json](#message-data) | 실험 질문·응답 6건; ID·시각 제외 |
| [data/evidence_manifest.json](#evidence-manifest) | 증거 파일 54개의 상대 경로·크기·SHA-256 |

원본 DB·WAL·SHM, 원본 history, 개인 절대 경로가 포함된 목록, 전체 프로세스 목록은 공개 자료에 포함하지 않습니다. 공개 결과만으로 원본 분석을 독립 재실행할 수는 없으며, 코드는 같은 구조의 증거 사본을 별도로 확보한 경우 실행할 수 있습니다.

Python 3.10 이상과 표준 라이브러리를 사용합니다.

```powershell
python scripts/analyze.py --source "D:\EvidenceCopy\OnPrem_AI_Forensics" --output "private\verification"
```

입력과 출력은 서로 다른 일반 디렉터리를 사용합니다. 심볼릭 링크·junction은 사용하지 않습니다. 분석 출력에는 실험 대화 본문이 포함되므로 공개 데이터와 별도로 관리합니다.

## 7. 다음 검증 방향과 GPT 활용

향후에는 실행 방식, 종료 방식, 대화 삭제 조건을 달리한 반복 실험을 통해 기록의 생성·변경·잔존 양상을 비교하고, 사용자 입력·AI 응답·실행 기록을 연결할 수 있는 범위와 한계를 검토하고자 합니다. 이는 후속 계획이며 이번 실험의 완료된 결과는 아닙니다.

실습 설계·자료 정리와 분석 코드 작성에는 GPT의 도움을 받았습니다. 실험 수행과 수집 자료를 바탕으로 결과를 정리했으며, 공유 준비 과정에서 파일 사본의 SQL 건수와 바이트 위치를 다시 확인했습니다. GPT의 설명 자체를 실험 근거로 사용하지 않았습니다.

## 8. 자료 바로 읽기

아래 자료는 위에서 안내한 파일 내용을 이 페이지에서 직접 읽을 수 있도록 함께 실었습니다. 각 제목 아래의 펼치기 항목을 누르면 전체 내용이 표시됩니다.

### conversation

<details>
<summary>실험 대화 기록 펼치기</summary>

# GUI 실험 대화 기록

기존 recovered_messages.csv의 6행에서 대화 ID·레코드 ID·시각을 제외하고 정리한 열람용 사본입니다. 질문과 응답 본문은 수정하지 않았습니다. 모델 응답의 내용은 실험 기록이며 사실 설명으로 채택하지 않습니다.

SQL 조회로 user 3건·assistant 3건을 재검증했습니다. 각 본문을 SQL에서 다시 추출해 CSV와 대조한 것은 아니며, 삭제 후 DB에서 대화 전체를 복원한 기록도 아닙니다.

## 1. 사용자 질문

```text
안녕하세요. 현재 실행 중인 AI 모델이 무엇인지 알려주세요.
```

## 2. AI 응답

저장된 모델명: `qwen2.5:0.5b`

```text
저는 AI 모델을 포함하는 "Qwen"라는 인공지능인 모델입니다. 현재 실행 중인 AI 모델은 "Qwen"입니다. 이 모델이 어떻게 작동하는지, 사용할 수 있는 다양한 기능을 제공하는지, 그리고 어떤 도움이 될 수 있는지에 대한 정보를 제공합니다.
```

## 3. 사용자 질문

```text
이번 실험의 식별문자열은 FORENSIC-TEST-2026-BETA입니다. 이 문자열을 기억해주세요. 
```

## 4. AI 응답

저장된 모델명: `qwen2.5:0.5b`

```text
알겠습니다, 기억했습니다. "FORENSIC-TEST-2026-BETA"입니다. 이는 AI 모델의 이름을 포함하는 문자열입니다.
```

## 5. 사용자 질문

```text
제가 앞서 기억해달라고 요청한 식별 문자열을 정확하게 다시 알려주세요.
```

## 6. AI 응답

저장된 모델명: `qwen2.5:0.5b`

```text
알겠습니다, "FORENSIC-TEST-2026-BETA"입니다. 이는 AI 모델의 이름을 포함하는 문자열입니다.
```



</details>

### methods

<details>
<summary>분석 방법과 검증 범위 펼치기</summary>

# 분석 방법과 검증 범위

## 입력 자료와 보존

1. 원본 디렉터리의 파일 54개를 읽어 SHA-256을 계산했습니다.
2. 작업 공간의 `private/evidence/`로 사본을 만들고 원본의 복사 전후 SHA-256 일치를 확인했습니다.
3. DB별로 db.sqlite, db.sqlite-wal, db.sqlite-shm을 별도 임시 폴더로 복사했습니다. SQLite 연결은 임시 사본에만 수행했습니다. WAL 처리가 원본에 영향을 주지 않도록 했습니다.
4. `sqlite_master`에서 테이블과 messages rootpage를 확인하고 messages 건수 및 role별 건수를 조회했습니다.
5. main DB의 원시 바이트에서 UTF-8 식별 문자열을 검색했습니다. SQLite 헤더의 페이지 크기를 이용해 페이지 번호와 B-tree 헤더의 셀 개수를 확인했습니다.
6. 분석에 입력한 사본의 전체 파일 해시도 분석 전후 일치했습니다.

## SQL 조회

각 스냅샷은 main DB와 같은 시점에 수집된 WAL·SHM을 함께 임시 폴더에 복사합니다. `PRAGMA query_only=ON`을 설정한 연결에서 다음 쿼리로 논리 상태를 확인합니다. SQLite의 WAL 처리와 연결 종료 영향은 임시 폴더에만 발생하도록 했습니다.

```sql
SELECT name FROM sqlite_master WHERE type = 'table';
SELECT count(*) FROM messages;
SELECT role, count(*) FROM messages GROUP BY role;
SELECT rootpage FROM sqlite_master WHERE name = 'messages';
```

`GUI_Experiment/Before`와 `Evidence/SQLite`는 0건, `GUI_Experiment/After`와 `Deletion_Experiment/BeforeDeletion`은 6건(user 3건, assistant 3건), `Deletion_Experiment/AfterDeletion`은 0건입니다.

## 바이트 검색과 페이지 해석

검색 대상은 임시 연결로 처리된 DB가 아니라, 입력 main DB의 원시 바이트입니다. UTF-8 문자열 `FORENSIC-TEST-2026-BETA`와 정확히 일치하는 위치를 검색했습니다. UTF-16, 변형 문자열, WAL 내부 문자열, 삭제 레코드의 필드 복원은 분석 범위에 포함하지 않았습니다.

SQLite 파일 헤더의 16–17번 바이트에서 페이지 크기를 읽습니다. 이번 파일은 4096바이트입니다. 파일 시작을 0으로 하는 오프셋에 대해 `페이지 번호 = offset // 4096 + 1`로 계산합니다.

삭제 후 오프셋 18915, 19416, 19686은 모두 5번 페이지입니다. 그 페이지의 B-tree 헤더 타입은 13(`0x0D`, 테이블 leaf), 셀 개수는 0입니다. `sqlite_master`에서 확인한 `messages` rootpage도 5입니다. 이를 근거로 현재 유효한 셀이 없는 messages 루트 페이지의 바이트에 문자열이 남아 있다고 기술했습니다. 각 문자열이 원래 어떤 레코드의 어느 필드였는지 모두 복원한 것은 아닙니다.

## 관찰과 해석의 구분

GUI After와 Deletion Before의 SQL 조회는 DB와 WAL을 합쳐 본 논리 상태입니다. 4KB main DB만으로는 해당 상태를 재현할 수 없습니다. AfterDeletion은 48KB main DB와 0바이트 WAL이며 식별 문자열 3곳이 같은 페이지에 있습니다. 이는 3개의 완전한 레코드 복원이나 세 번의 별도 행위를 의미하지 않습니다.

기존 `recovered_messages.csv`의 6행을 확인해 공유본을 작성했습니다. 현재 스크립트의 SQL 검증은 건수와 role 집계이며, 각 본문을 SQL에서 다시 추출해 CSV와 대조하는 작업은 수행하지 않았습니다.

수집 CSV의 당시 OriginalSHA256/CopySHA256 필드와 현재 manifest의 해시는 의미가 다릅니다. manifest는 이번 준비 시점의 파일 해시이며 최초 수집 순간의 무결성이나 전체 chain of custody를 소급해서 증명하지 않습니다.

원본 파일의 내용은 수정하지 않았습니다. 읽기 접근으로 발생할 수 있는 OS 메타데이터 변화까지 검증한 것은 아닙니다. 라이브 시스템의 당시 상태, GUI 삭제 동작, 종료 순서, SQLite 설정은 추가 반복 실험에서 통제해야 합니다.


</details>

### analysis-code

<details>
<summary>분석 스크립트 펼치기</summary>

```python
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
```

</details>

### verified-results

<details>
<summary>검증 집계 펼치기</summary>

```json
{
  "snapshots": [
    {
      "path": "Deletion_Experiment/AfterDeletion/db.sqlite",
      "page_size": 4096,
      "tables": [
        "settings",
        "chats",
        "messages",
        "sqlite_sequence",
        "tool_calls",
        "attachments",
        "users"
      ],
      "messages_count": 0,
      "roles": {},
      "messages_root_page": 5,
      "marker": "FORENSIC-TEST-2026-BETA",
      "main_db_marker_hits": [
        {
          "offset": 18915,
          "page": 5
        },
        {
          "offset": 19416,
          "page": 5
        },
        {
          "offset": 19686,
          "page": 5
        }
      ],
      "hit_page_headers": [
        {
          "page": 5,
          "btree_type": 13,
          "cell_count": 0,
          "is_messages_root": true
        }
      ]
    },
    {
      "path": "Deletion_Experiment/BeforeDeletion/db.sqlite",
      "page_size": 4096,
      "tables": [
        "settings",
        "chats",
        "messages",
        "sqlite_sequence",
        "tool_calls",
        "attachments",
        "users"
      ],
      "messages_count": 6,
      "roles": {
        "assistant": 3,
        "user": 3
      },
      "messages_root_page": 5,
      "marker": "FORENSIC-TEST-2026-BETA",
      "main_db_marker_hits": [],
      "hit_page_headers": []
    },
    {
      "path": "Evidence/SQLite/db.sqlite",
      "page_size": 4096,
      "tables": [
        "settings",
        "chats",
        "messages",
        "sqlite_sequence",
        "tool_calls",
        "attachments",
        "users"
      ],
      "messages_count": 0,
      "roles": {},
      "messages_root_page": 5,
      "marker": "FORENSIC-TEST-2026-BETA",
      "main_db_marker_hits": [],
      "hit_page_headers": []
    },
    {
      "path": "GUI_Experiment/After/db.sqlite",
      "page_size": 4096,
      "tables": [
        "settings",
        "chats",
        "messages",
        "sqlite_sequence",
        "tool_calls",
        "attachments",
        "users"
      ],
      "messages_count": 6,
      "roles": {
        "assistant": 3,
        "user": 3
      },
      "messages_root_page": 5,
      "marker": "FORENSIC-TEST-2026-BETA",
      "main_db_marker_hits": [],
      "hit_page_headers": []
    },
    {
      "path": "GUI_Experiment/Before/db.sqlite",
      "page_size": 4096,
      "tables": [
        "settings",
        "chats",
        "messages",
        "sqlite_sequence",
        "tool_calls",
        "attachments",
        "users"
      ],
      "messages_count": 0,
      "roles": {},
      "messages_root_page": 5,
      "marker": "FORENSIC-TEST-2026-BETA",
      "main_db_marker_hits": [],
      "hit_page_headers": []
    }
  ],
  "original_content_unchanged": true,
  "file_count": 54,
  "verification_date": "2026-10-12"
}
```

</details>

### message-data

<details>
<summary>대화 데이터 펼치기</summary>

```json
[
  {
    "sequence": 1,
    "role": "user",
    "content": "안녕하세요. 현재 실행 중인 AI 모델이 무엇인지 알려주세요.",
    "model_name": ""
  },
  {
    "sequence": 2,
    "role": "assistant",
    "content": "저는 AI 모델을 포함하는 \"Qwen\"라는 인공지능인 모델입니다. 현재 실행 중인 AI 모델은 \"Qwen\"입니다. 이 모델이 어떻게 작동하는지, 사용할 수 있는 다양한 기능을 제공하는지, 그리고 어떤 도움이 될 수 있는지에 대한 정보를 제공합니다.",
    "model_name": "qwen2.5:0.5b"
  },
  {
    "sequence": 3,
    "role": "user",
    "content": "이번 실험의 식별문자열은 FORENSIC-TEST-2026-BETA입니다. 이 문자열을 기억해주세요. ",
    "model_name": ""
  },
  {
    "sequence": 4,
    "role": "assistant",
    "content": "알겠습니다, 기억했습니다. \"FORENSIC-TEST-2026-BETA\"입니다. 이는 AI 모델의 이름을 포함하는 문자열입니다.",
    "model_name": "qwen2.5:0.5b"
  },
  {
    "sequence": 5,
    "role": "user",
    "content": "제가 앞서 기억해달라고 요청한 식별 문자열을 정확하게 다시 알려주세요.",
    "model_name": ""
  },
  {
    "sequence": 6,
    "role": "assistant",
    "content": "알겠습니다, \"FORENSIC-TEST-2026-BETA\"입니다. 이는 AI 모델의 이름을 포함하는 문자열입니다.",
    "model_name": "qwen2.5:0.5b"
  }
]
```

</details>

### evidence-manifest

<details>
<summary>증거 파일 목록과 SHA-256 펼치기</summary>

```json
[
  {
    "path": "Analysis/changed_files.csv",
    "bytes": 3,
    "sha256": "f1945cd6c19e56b3c1c78943ef5ec18116907a4ca1efc40a57d48ab1db7adfc5"
  },
  {
    "path": "Analysis/history_copy.txt",
    "bytes": 297,
    "sha256": "15d5e658daadaada5e061a43455ed82d1736d872bd3a7b9a0b2a01f0b45f25b8"
  },
  {
    "path": "Analysis/new_files.csv",
    "bytes": 328,
    "sha256": "05a3eb55f5ab2534393afbcfaf0de646a35a18a63e4d9b7ffc58a33d985f5d9e"
  },
  {
    "path": "Analysis/prompt_log_search.csv",
    "bytes": 3,
    "sha256": "f1945cd6c19e56b3c1c78943ef5ec18116907a4ca1efc40a57d48ab1db7adfc5"
  },
  {
    "path": "Deletion_Experiment/AfterDeletion/db.sqlite",
    "bytes": 49152,
    "sha256": "856fb982ec63a463501805c27da8fdc62f0f3643239b82a9153da42fb85a1be9"
  },
  {
    "path": "Deletion_Experiment/AfterDeletion/db.sqlite-shm",
    "bytes": 32768,
    "sha256": "fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb"
  },
  {
    "path": "Deletion_Experiment/AfterDeletion/db.sqlite-wal",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  {
    "path": "Deletion_Experiment/AfterDeletion/hashes.csv",
    "bytes": 519,
    "sha256": "29232cc020936dc498ca5b1f7c622c8b72d3a58b95f3018b4486f00af7d858aa"
  },
  {
    "path": "Deletion_Experiment/BeforeDeletion/db.sqlite",
    "bytes": 4096,
    "sha256": "352a9bb23c329c5a9bf235baf56917358b5b64b03f1a11d261fadae9c3cdb721"
  },
  {
    "path": "Deletion_Experiment/BeforeDeletion/db.sqlite-shm",
    "bytes": 32768,
    "sha256": "f166bc5b464783a4a059d08f2d1fe9c10e59a866124d70679bd0be8848dc2020"
  },
  {
    "path": "Deletion_Experiment/BeforeDeletion/db.sqlite-wal",
    "bytes": 861112,
    "sha256": "720bba193a0df871999d6e2e0f71a41b4ec8ad06dbc3594ace676fbfd61a8b84"
  },
  {
    "path": "Deletion_Experiment/BeforeDeletion/hashes.csv",
    "bytes": 519,
    "sha256": "eafa1cfb26762e2dd97e57abf3917cf758e765a40a41bfced3a0dd475e92ef66"
  },
  {
    "path": "Evidence/Before/all_processes.csv",
    "bytes": 31442,
    "sha256": "c1b8f0d6e5aeaac6e534241116f0a484ee51bc8d6b2eb57752a14d17ad1bc2e2"
  },
  {
    "path": "Evidence/Before/collection_time.txt",
    "bytes": 31,
    "sha256": "50d9556132d8dc075f1c2e32b634bc368b1a8ee2018bb9aaa706a70e45fd9cf0"
  },
  {
    "path": "Evidence/Before/ollama_paths.csv",
    "bytes": 154,
    "sha256": "7c12232c32fb683cd3ecd312dce59cfb9e6ad0b184fc3daa665b0d71b3d66c10"
  },
  {
    "path": "Evidence/Before/ollama_processes.csv",
    "bytes": 3,
    "sha256": "f1945cd6c19e56b3c1c78943ef5ec18116907a4ca1efc40a57d48ab1db7adfc5"
  },
  {
    "path": "Evidence/Before/system_info.txt",
    "bytes": 156,
    "sha256": "d56e13fb3e83b83ac8059b877d8311c60bcadfca78168a7e975d781e522e7c1c"
  },
  {
    "path": "Evidence/before_hashes.csv",
    "bytes": 460,
    "sha256": "d509bde1e1da914fb9c5368c91f586864cb14633ae94b4ff3cfbbd417139ae3a"
  },
  {
    "path": "Evidence/DuringRun/collection_time.txt",
    "bytes": 31,
    "sha256": "f833be1ef02378fc2c7a1053c4d64b6799274018956dc810aab8a91ca04d12b5"
  },
  {
    "path": "Evidence/DuringRun/processes.csv",
    "bytes": 604,
    "sha256": "70f3bcf75f0c0eb9ad8d0b38a017aecac12cbd82624c92b3b7e30416fd377db1"
  },
  {
    "path": "Evidence/DuringRun/running_models.txt",
    "bytes": 204,
    "sha256": "11bafe38d5ca2c3af190bdbe83dd32987037489fdc3dff107d1646dd0a6bb8c3"
  },
  {
    "path": "Evidence/history_original_hash.csv",
    "bytes": 118,
    "sha256": "ef73518d1db2881fc6761d9bdc203dcd357da72e402a8d013694010b5fb59b24"
  },
  {
    "path": "Evidence/Installed/collection_time.txt",
    "bytes": 31,
    "sha256": "18d5f53887861f8075332bbb5609f11015b9262a3e697dc14a200c95f3aaccff"
  },
  {
    "path": "Evidence/Installed/model_storage_before.csv",
    "bytes": 105,
    "sha256": "b795b38f50ca6e517557e798dc3bfa426743cd57cb10be0571760633268fe9a5"
  },
  {
    "path": "Evidence/Installed/models_before.txt",
    "bytes": 36,
    "sha256": "12e5c699129cd5c1dd89f6ddc1c9db8fe1976a99cb4f24b364ddd03b17bbb0c3"
  },
  {
    "path": "Evidence/Installed/ollama_files.csv",
    "bytes": 217027,
    "sha256": "5a99e649e9bf6633f707b344cb7b88728e023251e8755d91e65143493ee90429"
  },
  {
    "path": "Evidence/Installed/ollama_paths.csv",
    "bytes": 151,
    "sha256": "4d2c1745c8c8e123b88d2058537d42d1f57eef21a5b0bab3cda92ca9da104844"
  },
  {
    "path": "Evidence/Installed/ollama_processes.csv",
    "bytes": 348,
    "sha256": "595d66c78fbce30786ec43e4cdb509d46eeeae6428ae78d90bcf50ddc66cafaf"
  },
  {
    "path": "Evidence/Installed/ollama_version.txt",
    "bytes": 29,
    "sha256": "53526f2ad2b83b7da91621dca48a2293b0972dae6fc37136000d614a60832cb7"
  },
  {
    "path": "Evidence/PostRun/collection_time.txt",
    "bytes": 31,
    "sha256": "ecf998b7e43d9ae24220cfe0012156d7858b5b4d72ef1c55e1d7071d61939463"
  },
  {
    "path": "Evidence/PostRun/files.csv",
    "bytes": 2926,
    "sha256": "9d5cd40af605237e641f1da87609fc054e01115d8171826f0166cf452ac5e3a8"
  },
  {
    "path": "Evidence/PostRun/models.txt",
    "bytes": 124,
    "sha256": "f650b8ab586c1b171476bc288eb7f5090912b9d88dbc8f05832c80dca1d4ae76"
  },
  {
    "path": "Evidence/PostRun/processes.csv",
    "bytes": 277,
    "sha256": "23a2d2834d35617d6f67e26c5773e5cab4d995cfa997db3e6af54122d35a4e5d"
  },
  {
    "path": "Evidence/PostRun/running_models.txt",
    "bytes": 67,
    "sha256": "74fb76de226523fc8d508e3509e2cc20623bf29ebe03cf4c22c95c624605fe79"
  },
  {
    "path": "Evidence/PreRun/collection_time.txt",
    "bytes": 31,
    "sha256": "664020de0d140bc9551b79d61b097d244faa2b2c31680beb4a4006a0ebb2014b"
  },
  {
    "path": "Evidence/PreRun/files.csv",
    "bytes": 2659,
    "sha256": "6fda4587fa2e172759877206824f2fe4addec52d80c4f81c2951cd46df064094"
  },
  {
    "path": "Evidence/PreRun/models.txt",
    "bytes": 122,
    "sha256": "d172e64b12799f84ce3b6add50bdfacb75067a445db56a00d833db0dcfa837be"
  },
  {
    "path": "Evidence/PreRun/processes.csv",
    "bytes": 277,
    "sha256": "23a2d2834d35617d6f67e26c5773e5cab4d995cfa997db3e6af54122d35a4e5d"
  },
  {
    "path": "Evidence/PreRun/running_models.txt",
    "bytes": 67,
    "sha256": "74fb76de226523fc8d508e3509e2cc20623bf29ebe03cf4c22c95c624605fe79"
  },
  {
    "path": "Evidence/prerun_hashes.csv",
    "bytes": 442,
    "sha256": "b522433bb8eaafa9c1cd38223df44fc6e85079e3b5ca3766bf07328a6aaf3b93"
  },
  {
    "path": "Evidence/SQLite/db.sqlite",
    "bytes": 4096,
    "sha256": "352a9bb23c329c5a9bf235baf56917358b5b64b03f1a11d261fadae9c3cdb721"
  },
  {
    "path": "Evidence/SQLite/db.sqlite-shm",
    "bytes": 32768,
    "sha256": "907b5bffaff1e8ca08f7a9b5f69b00302f638c376ef115b8c32099237cb06172"
  },
  {
    "path": "Evidence/SQLite/db.sqlite-wal",
    "bytes": 119512,
    "sha256": "49504f28e5101366d5a775067130b0d13d78bbcbd2c246c31dcc046944b3a17b"
  },
  {
    "path": "Evidence/sqlite_hashes.csv",
    "bytes": 519,
    "sha256": "77bb49f91edcd423ba45344a162ee778d3da94f6882422aecd51794c9b5244c7"
  },
  {
    "path": "GUI_Experiment/After/db.sqlite",
    "bytes": 4096,
    "sha256": "352a9bb23c329c5a9bf235baf56917358b5b64b03f1a11d261fadae9c3cdb721"
  },
  {
    "path": "GUI_Experiment/After/db.sqlite-shm",
    "bytes": 32768,
    "sha256": "f166bc5b464783a4a059d08f2d1fe9c10e59a866124d70679bd0be8848dc2020"
  },
  {
    "path": "GUI_Experiment/After/db.sqlite-wal",
    "bytes": 861112,
    "sha256": "720bba193a0df871999d6e2e0f71a41b4ec8ad06dbc3594ace676fbfd61a8b84"
  },
  {
    "path": "GUI_Experiment/After/hashes.csv",
    "bytes": 519,
    "sha256": "ede620041fb48bbf8cab28b10cda0c911cc20ee4046738a0a85f69439e03f502"
  },
  {
    "path": "GUI_Experiment/Analysis/recovered_messages.csv",
    "bytes": 1453,
    "sha256": "f19f52283cbe4f06e96afcb0a57721f19e806b03ec7b9e9950b79988e00e05e6"
  },
  {
    "path": "GUI_Experiment/Before/db.sqlite",
    "bytes": 4096,
    "sha256": "352a9bb23c329c5a9bf235baf56917358b5b64b03f1a11d261fadae9c3cdb721"
  },
  {
    "path": "GUI_Experiment/Before/db.sqlite-shm",
    "bytes": 32768,
    "sha256": "907b5bffaff1e8ca08f7a9b5f69b00302f638c376ef115b8c32099237cb06172"
  },
  {
    "path": "GUI_Experiment/Before/db.sqlite-wal",
    "bytes": 119512,
    "sha256": "49504f28e5101366d5a775067130b0d13d78bbcbd2c246c31dcc046944b3a17b"
  },
  {
    "path": "GUI_Experiment/Before/hashes.csv",
    "bytes": 519,
    "sha256": "23f3fe9a5f644f759b1f5ab5d9ef6f5e717549b97ec0f38bb157d2edeae380b8"
  },
  {
    "path": "Reports/experiment_start.txt",
    "bytes": 31,
    "sha256": "12fb0f714eff149f02d339ca402cfee289f88d28d52cc3c4754ab5137408643e"
  }
]
```

</details>
