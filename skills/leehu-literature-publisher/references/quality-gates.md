# Quality gates and recovery

Use this release contract for the explicitly requested end-to-end publication.

## Baseline and authority gate

- AGENTS.md was read and the repository path, main branch, and GitHub Pages target were confirmed.
- The initial index is empty, or the user explicitly authorized the exact pre-existing staged set for this publication.
- main is checked out before changes; a branch switch occurred only from a clean tree and index under an explicit main-targeting request.
- origin/main was fetched and any clean behind state was fast-forwarded before generation.
- A local-ahead state stopped unless every pre-existing ahead commit was explicitly authorized and recorded separately.
- Divergence or overlapping incoming changes stopped the run unless a merge was explicitly authorized and all baseline facts were recomputed.
- The synchronized initial tracked and untracked status is recorded exactly.
- Unrelated unstaged or untracked work is absent or isolated by task-path non-overlap, tracked-diff content hash, and every untracked path/content hash with user authorization.
- The task includes explicit authority for commit, push, public deployment, and one IndexNow request.
- Authentication failure is diagnosed and reported; login or key changes require separate user approval.
- OCI, Ubuntu, Tailscale, and other deployment hosts are not used.
- The checkpoint is outside the repository and contains no credentials.

## Source and content gate

- Requested count equals manifest count.
- Every full review batch contains 50 notes; only the final batch may be smaller.
- IDs are contiguous and all date-bearing values use the actual KST publication date.
- Existing IDs, slugs, and titles do not collide.
- Source fields intended to be unique have no duplicates: id, slug, title, introduction or quote, commentary, closing, source_location, translation_note, rights_note, and each semantic-section text.
- Repeating author, source work, tags, and publication date is allowed by design.
- The source schema was not expanded with canonical or meta-description keys unless those keys already existed.
- Builder-derived canonical URLs and meta descriptions are unique and match their source notes.
- Each note has work_introduction, why_read_now, personal_reflection, and meaning_today.
- Commentary and every section meet repository sentence and length gates.
- Exact sentence reuse at 25 characters or longer is zero.
- Variable-normalized template-skeleton reuse is zero within the generated batch.
- If N is at least 50, at least 20 interpretive lenses and five article flows are distributed across the whole manifest; otherwise require min(20, N) lenses and min(5, N) flows.
- Three consecutive notes do not share the same flow.
- All 50-note review units, plus a possible smaller final unit, pass before one whole-manifest apply.
- Korean particle, incomplete-ending, and awkward substitution errors are zero.
- Internal production terminology is absent from public copy.
- Unsupported plot, character, ending, scene, and author-intent claims are absent.
- Direct quotations are absent unless permission and provenance are verified.
- Rights and source notes are accurate.
- Generator output and manifest are semantically identical after canonical JSON serialization.
- An independent reviewer passed all batches and the first, middle, last, and work-stratified samples.
- Blocker and high-severity issue counts are zero.

## Concentration gate

Let T be the proposed final source count before apply.

- Concentration is calculated on the complete proposed manifest before apply.
- The most common source_work count divided by T is within the builder's work limit.
- The most common tag share is within the builder's tag limit.
- Lee Hu alone may be excluded from the author concentration rule for the official archive.
- Lee Hu works and tags remain subject to concentration rules.
- Any required redistribution is completed in the manifest and re-reviewed before apply.
- Expected list pages equal ceil(indexable_count / PAGE_SIZE).
- Expected sitemap size comes from the produced sitemap and retains auxiliary URLs.

## Apply, build, and static-output gate

- literature_batch.py append passes without --apply before it runs with --apply.
- Before apply, the canonical manifest hash, planned file list, prior target states, and backup mapping are atomically checkpointed.
- The complete manifest is applied once after all unit and global gates pass.
- After apply, the applied file-list hash and canonical post-apply file-hash set are checkpointed.
- Source JSON count equals the builder's expected count.
- Source and detail slug sets match exactly.
- Indexable and noindex totals match the versioned policy.
- Pagination count and cards per page are correct.
- RSS contains the full indexable set and all new indexable URLs.
- Sitemap URLs are unique, preserve auxiliary pages, and contain every new indexable URL.
- Homepage latest cards and visitor-board integration remain valid.
- Search indexes author, work, title, and tags.
- Every new detail has matching canonical, meta description, Open Graph, and valid JSON-LD.
- Every new detail renders commentary and all four semantic sections.
- Every original-reflection introduction is a reflection-deck paragraph, never a blockquote.
- A browser mobile viewport reports at least 48px computed separation between consecutive commentary sections.
- One explicit production build completes after changes are final.
- Full tests pass when generator, renderer, common CSS, tests, or index policy changed; otherwise the relevant regression suite passes. Syntax checks, batch verification, and git diff --check always pass.

## Git and deployment gate

- origin/main was fetched immediately before staging.
- A changed remote was safely integrated and affected gates rerun, or publication stopped.
- Only explicit task paths are staged; git add -A is not used.
- The staged name set equals the checkpointed planned_task_files set exactly.
- Staged files and diff were inspected.
- No credentials, private keys, tokens, checkpoints, or temporary backups are staged.
- The commit is on main with a clear Korean message.
- Push succeeds without force.
- The selected Pages run is the run whose headSha equals the pushed SHA; runs for other commits are ignored.
- Polling uses 10–30 second intervals with a 15-minute deadline.
- GitHub Pages reports success and deployed headSha equals the pushed SHA.
- Missing, failed, mismatched, or superseded matching runs stop publication reporting.

## Public gate

- Homepage, literature index, RSS, sitemap, and min(5, N) representative details return HTTP 200 first.
- Every new detail is checked with concurrency no greater than 8.
- Requests use a 20-second timeout and at most three bounded transient retries.
- Every new detail matches its source title, canonical, commentary, four sections, and JSON-LD.
- No new public original-reflection detail uses a blockquote introduction.
- Public RSS and sitemap contain the exact new slug set.
- Pages still reports the pushed SHA after exhaustive checks.
## IndexNow gate

- IndexNow runs only after every deployment and public gate succeeds.
- The repository's existing approved helper is used and inspected to ensure internal HTTP retries are disabled.
- The key is neither printed nor copied into logs or checkpoints.
- The payload contains deduplicated new detail URLs and actually changed list or pagination URLs only.
- The canonical payload SHA-256 is recorded before submission.
- Before helper launch, the checkpoint is atomically set to in_flight with attempt_count 1.
- Exactly one network attempt is made.
- Any in_flight, attempted, succeeded, failed, or unknown state forbids automatic resubmission on resume.
- A definitive response is recorded; an ambiguous outcome becomes unknown and is reported.

## Recovery checkpoint

Record all of these fields:

- task_id and target_count
- initial_status and starting_head
- planned_task_files and planned_task_files_sha256
- source_range and id_range
- generator_sha256 and manifest_sha256
- pre_apply_manifest_sha256 and previous_applied_manifest_sha256
- applied_file_list, applied_file_list_sha256, and post_apply_file_hashes_sha256
- backup_mapping
- tracked_diff_sha256 and untracked_path_content_sha256
- gate_input_hashes mapping each gate name to its canonical input SHA-256
- completed and remaining gates
- exact_url_set_sha256
- pushed_sha
- pages_run and pages_head_sha
- public_result_path and public_result_sha256
- passed_url_set_sha256 and failed_url_set_sha256
- indexnow_payload_sha256, attempt_count, indexnow_response, and indexnow_state

At the start of every run or resume, read this reference, then compare the checkpoint with Git, GitHub Pages, and the public site. Reuse a successful build, push, or deployment only when its complete input hash or commit SHA is unchanged; changed input invalidates it and all downstream gates. Never repeat any IndexNow attempt automatically.

If KST changed before commit, use checkpointed manifest and file hashes plus backup mapping to identify only proven batch-owned output. Move that output to a unique Windows temporary backup, regenerate all date-bearing values, and rerun review, dry-run, one whole-manifest apply, build, and affected tests. If regeneration or apply fails, restore only the proven backup mapping, verify prior hashes, and stop.

If any applied uncommitted batch must be regenerated, compare every target with the explicitly recorded previous-applied state and post-apply hashes. Never infer ownership from the current manifest alone, and never delete or overwrite unrelated content.
## Final state gate

- Final status equals the initial unrelated baseline.
- If initial status was clean, final worktree is clean.
- Local HEAD equals origin/main.
- Checkpoint contains final Pages, public verification, and IndexNow evidence.
- The reusable skill itself passed format validation and an independent forward test.

## Final report fields

- 신규 게시 수:
- 사용한 작품과 작품별 수량:
- 신규 ID/slug 범위:
- 주요 품질검사 결과:
- Build/Test 결과:
- 변경 파일:
- Commit SHA:
- Push 결과:
- GitHub Pages 결과:
- 공개 검증 URL 수:
- RSS/Sitemap 반영:
- IndexNow 제출 결과:
- 기존 기능 보존 확인:
- 스킬화 결과:
- 미결 사항:
