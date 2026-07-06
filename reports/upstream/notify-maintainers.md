# Maintainer notification — templates (not sent)

Short, friendly templates to use **when you file** the drafts in this directory.
Nothing here has been sent; filing requires repo access and is left to a human.
Keep each issue to one root cause, link the spec section, and include the minimal
reproducer from the matching draft.

## Issue body skeleton

```
**Environment:** <parser> <version>, Python 3.11, CommonMark spec 0.31.2

**Summary:** <one sentence>

**Reproducer:**
​```python
<minimal repro from the draft>
​```
- Expected: <spec-correct output> (matches cmark 0.31.2 and <other parser(s)>)
- Actual:   <observed output>

**Spec:** <section / example number>

Found via differential testing against the spec + the cmark reference
(<harness link, optional>). Happy to send a failing test case or a PR.
```

## Courtesy note (optional, for a maintainer DM / discussion)

> Hi — I ran a differential conformance + fuzzing harness across the maintained
> pure-Python CommonMark parsers against spec 0.31.2 and found a few small
> divergences (and one crash) in <parser>. I've written minimal, spec-cited
> reproducers and would be glad to open issues / PRs with failing test cases.
> No rush, and thanks for maintaining <parser>.

## Disclosure reminder

- These are **correctness/robustness** bugs (incl. a crash on untrusted input) —
  fileable publicly.
- If a future run finds a **sanitization bypass**, do **not** open a public
  issue: contact the maintainer's private security channel first (spec §6). The
  `cm-difftest security` command writes such findings only to the git-ignored
  `findings/` directory.
