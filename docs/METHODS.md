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
