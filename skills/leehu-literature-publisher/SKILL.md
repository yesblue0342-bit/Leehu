---
name: leehu-literature-publisher
description: Execute an explicitly requested end-to-end publication of a batch of novelist Lee Hu original-work literature notes in the Windows C:\codex\Leehu repository, including independent review, static build, a user-authorized main push, GitHub Pages verification, exhaustive public URL checks, and a user-authorized single IndexNow submission. Use only when the user requests this complete publishing workflow, not for a read-only audit, isolated verification, or IndexNow-only work.
---

# Lee Hu Literature Publisher

Complete the explicitly requested publication pipeline. A draft, plan, successful build, or successful push alone is not completion.

## Scope and authority

- Work only in the Windows repository C:\codex\Leehu.
- Read AGENTS.md before changing files and follow its repository instructions.
- Never connect to OCI, Ubuntu, Tailscale, or another deployment host.
- Use existing Git, GitHub CLI, and SSH authentication. If authentication fails, diagnose and report it; change login, keys, or credentials only after separate user approval.
- Never force-push, reset hard, rebase, or delete branches or tags.
- Treat main as the publication branch and GitHub Pages as the deployment target.
- Commit, push, public publication, and IndexNow are mutations. Perform each only when the user explicitly requested the end-to-end workflow.
- For a partial or read-only request, do only that scope and do not escalate into publication.

## Establish a safe baseline

1. Record a task ID, pre-fetch git status including the index, current branch, local HEAD, origin/main, recent Pages state, and the actual Asia/Seoul time.
2. Require an empty initial index. If any pre-existing change is staged, stop before mutation unless the user explicitly authorizes that exact staged set for this publication.
3. Require main before changes. If another branch is checked out, switch only when its tree and index are clean and the user's request explicitly targets main; otherwise stop.
4. Fetch origin main and compare SHAs before generation.
5. If a clean main is behind, fast-forward only, then recompute repository counts, ID and slug ranges, policies, and recent approved inputs.
6. If local main is ahead, stop unless the user explicitly authorizes publishing every pre-existing ahead commit; record those SHAs separately from the task commit.
7. If history diverged or local changes overlap incoming changes, stop. Merge only with explicit user approval, then rerun all baseline discovery.
8. After synchronization, record starting_head and the complete tracked and untracked initial_status.
9. If unrelated unstaged or untracked changes exist, proceed only when task paths do not overlap and a tracked-diff content hash plus every untracked path and content hash can be preserved; otherwise stop before mutation.
10. Preserve all pre-existing tracked, untracked, and user-authored files.
11. Create a JSON checkpoint in the Windows temporary directory, never inside the repository.
The checkpoint must contain task_id, target_count, initial_status, starting_head, planned_task_files and its hash, source and ID ranges, generator_sha256, manifest_sha256, pre_apply_manifest_sha256, previous_applied_manifest_sha256, applied_file_list and its hash, post_apply_file_hashes_sha256, backup_mapping, tracked_diff_sha256, untracked_path_content_sha256, gate_input_hashes mapping each gate to a canonical input SHA-256, completed and remaining gates, exact URL-set hash, pushed SHA, Pages run and headSha, public result-file path and hash, passed and failed URL-set hashes, and IndexNow payload hash, attempt count, response, and submission state.

Read references/quality-gates.md at the start of every run and resume, then update the checkpoint after every irreversible or expensive gate. Write checkpoint state atomically. On resume, reuse a successful gate only when its complete input hash or commit SHA is unchanged; any changed input invalidates that gate and every downstream gate.

## Date and source generation

- Use the actual KST public-deployment date in new IDs, slugs where dated, published_at, sitemap lastmod, tests, and core-page dates.
- Recheck KST immediately before commit. If the date changed after apply, use checkpointed pre-apply and previous-applied manifest hashes, applied file hashes, and backup mapping to move only proven batch-owned files to a unique temporary backup. Regenerate every date-bearing output and rerun independent review, dry-run, one whole-manifest apply, build, and all affected tests. If regeneration or apply fails, restore only the proven backup mapping, verify the recorded prior hashes, and stop.
- Define the newest approved generator and schema as the newest repository versions referenced by the latest passing regression tests or the latest dated approved batch that those tests cover.
- Reuse the approved generator, schema, builder, and reviewer patterns.
- Use only Lee Hu works and bibliographic facts already verified in the repository.
- Do not invent characters, events, endings, scenes, publication details, creative background, or authorial intent.
- Frame limited readings as the interpretation of the current note.
- Do not quote source prose without verified permission and provenance.
- Keep AI, automation, agent, reviewer, validation-tool, and SEO terminology out of public copy.
- Generate and independently review consecutive 50-note units; the final unit may contain fewer than 50.
- Do not apply units separately. After every unit and the global concentration gate pass, apply the complete requested manifest once.
- Across a target of at least 50 notes, distribute at least 20 interpretive lenses and five article flows. For a smaller target, require at least min(20, N) lenses and min(5, N) flows across the whole manifest.

Each source note needs a readable unique slug, original introduction, commentary, closing, source location, translation note, rights note, tags, related work, and the four keys work_introduction, why_read_now, personal_reflection, and meaning_today. Do not add canonical or meta-description keys unless the existing source schema defines them.

Require uniqueness only for source fields intended to be unique: id, slug, title, introduction or quote, commentary, closing, source_location, translation_note, rights_note, and each semantic-section text. Author, source work, tags, and publication date may repeat. Separately require builder-derived canonical URLs and meta descriptions to be unique and consistent with their source notes.

## Independent review

Use a reviewer independent from generator checks. Compare generator output and manifest by semantic deep equality after canonical JSON serialization; do not rely on file-byte formatting.

For every batch, inspect all automated gates plus the first, middle, last, and work-stratified samples. Require:
- no collisions with existing IDs, slugs, or titles;
- zero repeated exact sentences of 25 or more characters;
- zero repeated variable-normalized sentence skeletons in the generated batch;
- grammatical Korean particles, complete endings, and natural substitutions;
- repository-compliant commentary sentence count and length;
- all four sufficiently developed semantic sections;
- no unsupported story claim, copied prose, or internal production wording;
- an accurate no-direct-quotation rights disclosure when applicable; and
- coherent alignment among title, introduction, commentary, and sections.

A blocker or high-severity issue stops application. Fix the generator, regenerate the complete affected batch, and repeat generator and independent reviews. Do not hand-edit large manifests.

## Concentration gate before apply

Calculate concentration using the proposed final total T before writing source files.

- Enforce the builder's work and tag concentration limits.
- Only Lee Hu's author concentration exception may remain for this official archive.
- Do not exclude Lee Hu works or tags.
- Redistribute among verified works before apply if a work would exceed its limit.
- Derive expected list pages as ceil(indexable_count / PAGE_SIZE).
- Derive the sitemap total from produced output, not from an assumed fixed auxiliary count.

Read references/quality-gates.md before applying the manifest.

## Apply, build, and test

1. Run literature_batch.py append with no --apply and require a clean dry-run.
2. Before apply, atomically checkpoint the canonical manifest hash, planned file list, prior state or absence of every target, and any temporary-backup mapping.
3. Apply the complete manifest once only after every review unit and the global concentration gate pass.
4. Immediately checkpoint the applied file list and canonical post-apply file-hash set.
5. Do not run curate_literature.py if it could remove appended content.
6. Recalculate and update total, indexable, noindex, pagination, RSS, sitemap, and KST core-page expectations together.
7. Run one explicit production static build after source and shared-renderer changes are final.
8. Run the full suite when the generator, renderer, common CSS, tests, or index policy changed. A test may rebuild to verify idempotence; that does not replace or duplicate the explicit production build.
9. Run syntax checks, the batch verifier, and git diff --check.

## Verify local output

Check all new source and detail pages, not samples. Require source/detail slug equality, expected list pages, RSS and sitemap inclusion, title, body, canonical, meta description, Open Graph, valid JSON-LD, commentary, and all four sections.
Require original-reflection introductions to use a normal paragraph with class reflection-deck and never blockquote. Use a real browser viewport to confirm the computed mobile gap between consecutive commentary sections is at least 48px; CSS-source presence alone is insufficient. Verify homepage cards, author/work/title/tag search, pagination, internal links, and the visitor board.

## Commit and deploy safely

1. Fetch origin main immediately before staging and compare SHAs.
2. If origin advanced, inspect and integrate only with a safe fast-forward or an explicitly authorized merge. Recompute IDs, counts, policy totals, and rerun every affected gate; otherwise stop.
3. Stage only explicit task paths. Never use git add -A for this workflow.
4. Require the staged name set to match planned_task_files exactly. Inspect its diff, run a secret scan without printing secret values, and exclude checkpoints and temporary backups.
5. Commit on main with a clear Korean message and push without force.
6. Select the Pages build or workflow run whose headSha equals the pushed SHA; ignore runs for other commits.
7. Poll at intervals no shorter than 10 seconds for at most 15 minutes. Require success for the matching SHA.
8. If no matching run appears, it fails, its SHA differs, or a later commit supersedes the deployment before validation, stop and report rather than claim success.

## Verify public deployment

First check the homepage, literature index, RSS, sitemap, and min(5, N) representative new pages. Then scan every new page with maximum concurrency 8, a 20-second request timeout, and no more than three bounded retries with backoff for transient failures.

Require HTTP 200, source-matching title and canonical, commentary, all four semantic sections, valid JSON-LD, and no blockquote introduction. Save passed and failed URL lists in a durable temporary result file and checkpoint its path, hash, and both URL-set hashes. Confirm public RSS and sitemap contain the exact new slug set and Pages still reports the pushed SHA. A non-transient content mismatch requires a corrective commit, a matching Pages deployment, and a complete new public scan before IndexNow.

## Submit IndexNow exactly once

Only after Pages and all public checks succeed:

- Reuse the repository's approved IndexNow helper and never print or expose its key.
- Inspect the helper first and disable or avoid internal HTTP retry behavior; the launch may perform only one network attempt.
- Deduplicate the exact set of new detail URLs and changed list or pagination URLs.
- Canonically serialize the payload and record its SHA-256.
- Atomically set submission state to in_flight, attempt_count to 1, and persist the payload hash before launching the helper.
- Launch the helper exactly once, then record status and response evidence.
- Any state of in_flight, attempted, succeeded, failed, or unknown forbids automatic resubmission on resume.
- If the process ends without definitive evidence, mark it unknown and report it for user decision.

## Finish

Compare final status with initial_status. If the initial tree was clean, require a clean tree; otherwise require the unrelated baseline to be preserved exactly. Require local HEAD to equal origin/main, update the checkpoint, and report every field in references/quality-gates.md, including skill validation and unresolved items.
