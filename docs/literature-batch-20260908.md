# 2026-09-08 문학노트 추가 배치

- 원본 5,131건에 새 글 1,000건을 추가하여 총 6,131건을 유지한다.
- 새 원본 파일은 `content/literature/5132.json`부터 `6131.json`까지이다.
- 새 ID는 `20260908_leehu_literature_2761`부터 `3760`까지이다.
- 시집 《Fantasy》 400건, 《연(戀)》 200건, 《데자뷔》·《소나기》·《환상》·《별이 빛나는 밤에》 각 100건이다.
- 기존 글과 색인 정책은 유지한다. 공개 발견 대상은 5,632건, 기존 noindex 글은 499건이다.
- 《환상》과 《Fantasy》는 서로 다른 도서 URL을 사용한다. 감상 소재를 작품의 실제 장면이나 직접 인용으로 제시하지 않는다.

## 생성 및 검증

기존 9월 3일 생성기의 스키마·조사 처리·문장 검증을 재사용한다. 이번 배치의 별도 소재와 분포는 새 스크립트에 둔다. 기존 생성기의 소재나 기존 JSON은 바꾸지 않는다.

```bash
python scripts/append_leehu_works_20260908_1000.py
python scripts/literature_batch.py append content/leehu-works-20260908-1000.json
python scripts/literature_batch.py append content/leehu-works-20260908-1000.json --apply
python scripts/literature_batch.py build --expected-count 6131 --test
```

이미 추가된 뒤에는 append를 다시 실행하지 않는다. 생성기 재실행은 배치가 동일한지 확인하고 manifest만 재생성한다.

## 공개 및 OCI 사본

현재 www 도메인의 공개 원본은 GitHub Pages이다. main 푸시 후 Pages 배포를 확인한다. 이 저장소에는 현재 OCI Actions workflow가 없으며, 이번 작업에서 workflow나 DNS를 변경하지 않는다.

OCI 접속은 NUC의 `leehu-oci` 별칭을 사용한다. NUC의 Windows OpenSSH 실행 파일이 오류 255를 반환할 경우, 동일한 별칭과 기존 접속 설정을 사용하는 Git 배포본의 SSH 실행 파일을 사용할 수 있다.

OCI 원본 체크아웃은 `/home/ubuntu/Leehu`이다. main을 fast-forward로 반영한 뒤 같은 커밋으로 Docker 이미지를 빌드한다. 정적 사본은 `leehu-static` 컨테이너에서 실행하고, 서버 내부 `127.0.0.1:8980`으로 확인한다. 기존 공개 도메인 경로 및 다른 서비스는 유지한다. Docker 이미지에는 문학노트와 함께 기존 작품 안내 및 llms.txt도 포함한다.
