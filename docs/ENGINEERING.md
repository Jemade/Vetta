# Engineering notes: Vetta

## Purpose and scope

Interview assessment and scorecard review. This repository is an independently inspectable project; customer adoption, production scale and commercial readiness are not claimed without evidence.

## Request and data flow

Interview/artifact intake → persisted records → heuristic or provider review stages → structured scorecard → review console.

## Implementation map

Primary implementation and review locations: `app/agents`, `app/api`, `app/db`, `app/services`, `tests`. Dependency manifests and `.github/workflows/` specify installation and automated checks. Read the source for exact contracts and data models.

## Local verification

From `.` in a configured virtual environment:

```sh
pip install -r requirements.txt
pytest -q tests
```

From the repository root, run `python scripts/repository_check.py` for documentation and tracked-file checks. CI evidence is available in [GitHub Actions](https://github.com/Jemade/Vetta/actions). Green hygiene checks alone do not mean application tests passed.

## Decisions and boundaries

Scorecards are review aids, not validated hiring predictions. Provider keys are optional for heuristic tests. Public deployment requires an authentication, privacy and storage review.

Use the README's current run instructions and configuration examples. Keep provider credentials outside Git. Test changes against controlled fixtures before enabling external services. Health checks indicate process/service state, not end-to-end correctness.

## Review and operational evidence

[Review checklist](REVIEW_CHECKLIST.md) distinguishes repository evidence from outstanding human and deployment validation. Report measured workload, environment and method with any performance claim. Document incident fixes through reproducible issues and regression tests; do not invent user counts or peer reviews.

## Reuse and licensing

No repository-wide reuse license has been selected. Public visibility alone does not grant an open-source reuse license. Ownership and third-party asset rights must be confirmed before licensing this project.
