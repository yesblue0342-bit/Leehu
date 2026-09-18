# 2026-09-18 문학노트 50편

## 범위

- 기존 6,131편을 보존하고 50편을 추가한다. 새 전체 수량은 6,181편이다.
- 원본 파일: `content/literature/6132.json`부터 `6181.json`까지.
- ID: `20260918_leehu_literature_3761`부터 `3810`까지.
- 《연(戀)》와 《데자뷔》 각 9편, 《소나기》·《환상》·《별이 빛나는 밤에》·《Fantasy》 각 8편.
- 앞의 세 작품은 소설, 뒤의 세 작품은 시집이다. 《환상》과 《Fantasy》의 서점 URL을 구분한다.
- 기존 색인 정책은 변경하지 않는다. 공개 발견 대상 5,682편, 기존 `noindex` 499편, 목록 228쪽이다.
- 사이트맵은 실제 부가 페이지 26개를 보존하여 5,713개 URL을 포함한다.

## 원고 원칙

이번 원고는 확인된 저자·제목·장르를 바탕으로 세운 독립적인 독서 질문이다. 작품 본문의 인물·사건·결말이나 작가의 의도, 실제 체험을 추정하지 않는다. 본문 직접 인용과 번역문 전재는 없다.

50개의 개별 원고는 `scripts/leehu_notes_20260918_a.py`, `b.py`, `c.py`에 둔다. 문장을 소재 이름으로 치환하는 방식이 아니라 각 질문의 논점을 따로 전개한다. 기존 20개 필드의 원본 스키마와 네 가지 의미 섹션을 유지하며, 공개 원본에 별도의 관리용 필드를 추가하지 않는다.

## 재현과 검증

```powershell
python -X utf8 scripts/append_leehu_works_20260918_50.py
python -X utf8 scripts/review_leehu_works_20260918_50.py
python -X utf8 scripts/literature_batch.py append content/leehu-works-20260918-50.json
# 최초 게시 시 독립 검토 후 한 번만 실행한다.
python -X utf8 scripts/literature_batch.py append content/leehu-works-20260918-50.json --apply
python -X utf8 scripts/literature_batch.py build --expected-count 6181
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/literature_batch.py verify --expected-count 6181
```

이미 적용된 원본에는 append를 다시 실행하지 않는다. 생성기와 독립 검사기는 적용된 50개 원본이 manifest와 같은지도 확인한다. 기존 홈페이지 디자인, 방명록, 탐색 기능과 다른 글의 원문은 수정하지 않는다.

공개 원본은 GitHub Pages의 `main`이다. 배포된 커밋과 공개 페이지를 확인한 다음 새 상세 및 변경된 목록 URL만 한 번 알린다. 비밀키, 임시 검사 결과, 배포 체크포인트는 이 저장소에 포함하지 않는다.
