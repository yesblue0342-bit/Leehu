# 2026-09-23 이후 작품 문학노트 1,000편

## 발행 범위

- 기존 6,191편에 1,000편을 추가한다. 전체 7,191편, 색인 대상 6,692편, 기존 비색인 499편이다.
- 원본 파일은 `content/literature/6192.json`부터 `7191.json`까지다.
- ID는 `20260923_leehu_literature_3821`부터 `20260923_leehu_literature_4820`까지다.
- 날짜는 한국 시각 2026-09-23이다. `published_at`과 상세 페이지 구조화 데이터 및 사이트맵 날짜를 함께 적용한다.
- 작품별 신규 수량: 《연(戀)》 150편, 《데자뷔》 130편, 《소나기》 130편, 《환상》 130편, 《별이 빛나는 밤에》 130편, 《Fantasy》 330편.
- 기존 작품별 집중도 제한 12%를 유지한다. 비색인 정책은 바꾸지 않는다.
- 25편씩 268개 목록 페이지에 배치한다. RSS와 사이트맵에는 신규 상세 1,000개를 모두 포함한다.

## 원고와 출처

확인된 저자·작품명·장르에서 출발한 독립적인 독서 질문과 성찰이다. 작품 본문의 직접 인용이나 줄거리 재구성이 아니며, 인물·사건·결말·창작 의도·개인적인 과거 경험을 만들어 사실처럼 쓰지 않는다. 상상의 상황은 현재 노트의 사유 또는 가정으로 구분한다. 출처는 기존에 확인된 교보eBook의 작품별 서지를 사용한다.

원고는 관계와 대화, 기억과 시간, 날씨와 감각, 상상과 언어, 일상과 독서 습관으로 나뉜다. 각 노트에는 도입, 해설, 마무리, 출처, 번역 및 권리 메모, 태그, 관련 작품과 네 의미 항목을 둔다. 9월 22일부터 사용한 `work_anchor`를 유지하여 공식 작품 페이지의 도서 식별자와 연결한다.

`scripts/leehu_notes_20260923_a.py`부터 `e.py`까지가 원고 입력이며, 조립기는 기존 공개 스키마로 변환한다. 생성기의 자체 검사와 별도로 독립 검사기가 50편 단위 20개 묶음과 전체 중복·출처·문장·집중도를 검사한다. 모든 묶음을 통과한 전체 manifest를 한 번에 적용한다.

## 재현 및 검증

```powershell
python -X utf8 scripts/append_leehu_works_20260923_1000.py
python -X utf8 scripts/review_leehu_works_20260923_1000.py
python -X utf8 scripts/literature_batch.py append content/leehu-works-20260923-1000.json
# 최초 적용에만 --apply를 사용한다. 게시된 원본에는 다시 실행하지 않는다.
python -X utf8 scripts/literature_batch.py append content/leehu-works-20260923-1000.json --apply
python -X utf8 scripts/literature_batch.py build --expected-count 7191
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/literature_batch.py verify --expected-count 7191
```

발행 체크포인트, 검사 로그, 공개 URL 검사 결과는 저장소 밖 Windows 임시 디렉터리에 보관한다. 최종 발행에서는 커밋 SHA와 일치하는 GitHub Pages 배포를 확인하고, 신규 1,000개 공개 URL의 본문·canonical·JSON-LD와 RSS/사이트맵 수록 여부를 전수 검사한다. 이후 신규 상세와 실제 변경된 목록 URL에 대해서만 IndexNow를 한 번 호출한다.
