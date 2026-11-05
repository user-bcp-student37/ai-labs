# Design

## Context

- Issue #22 identifies `auth/` and `POST /auth/login` as the affected component and endpoint. See `proposal.md` for motivation and `specs/auth-login/spec.md` for observable requirements.
- `AuthResource` validates the request and delegates credential lookup to `LegacyDatabase.findByCredentials`. That lookup currently interpolates both credentials into SQL executed through JDBC `Statement`.
- `AuthResource` already distinguishes invalid requests (400), unmatched credentials (401), and successful authentication (200). The existing success response includes `user.username` and `token`.
- `docs/ENDPOINTS.md` does not document the auth endpoint. Its API contracts remain unchanged; the login success assertions in `AuthResourceTest` and the approved delta spec are the baseline for this design.

## Goals / Non-Goals

**Goals:**

- Make credential values data rather than executable SQL while retaining the existing account lookup behavior.
- Preserve the endpoint and response behavior required by the approved spec.
- Keep the change local to `auth/`, with no new dependency or database migration.

**Non-Goals:**

- Change token generation, token lifetime, response fields, request shape, or credential policy.
- Refactor authentication into new layers or change the `api/` or `web/` components.
- Revise the general endpoint documentation or resolve unrelated security findings.

## Protected Contracts

- Valid workshop credentials continue to return HTTP 200 with `user.username` and a non-empty `token`.
- The Issue's SQL-injection string used as either username or password returns HTTP 401 and no token. This is the intentional behavior change specified by Issue #22.
- Existing request validation and the response mapping in `AuthResource` remain unchanged; this work does not redefine its 400 and ordinary invalid-credential 401 behavior.
- No requirements are inferred from `docs/ENDPOINTS.md` for `/auth/login`, because it currently documents only `api/` contracts.

## Components Affected

- `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`: the credential lookup query and its JDBC execution.
- `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`: endpoint-level characterization and regression coverage.
- `AuthResource` and `LegacyTokenUtil` are contract boundaries to preserve, not intended change targets.

## Decisions

1. Bind `username` and `password` as JDBC query parameters using `PreparedStatement`. This keeps SQL structure fixed while preserving exact-value matching. Escaping or rejecting a blacklist of suspicious strings is less reliable because it depends on recognizing every SQL syntax variant.
2. Keep response and error mapping in `AuthResource` unchanged. The database lookup should return no matching user for non-matching literal credentials, allowing the existing 401 path to satisfy the spec without changing the success response or token behavior.
3. Keep the existing SQLite schema and dependencies. An ORM, a new persistence layer, or schema changes would add scope without helping this single credential query.

## Incremental Strategy

1. Add endpoint tests before changing the lookup: characterize valid login, existing invalid-request behavior, and ordinary invalid credentials. Add regression cases for the Issue's string in the username and password; those new security assertions are expected to fail against the vulnerable behavior.
2. Change only the credential lookup to bind both values, keeping selected columns, exact-match semantics, and the `UserRecord` mapping intact.
3. Run the auth component's Maven test suite from `auth/`; verify the valid-login and both injection cases, then review that no files outside `auth/` or this OpenSpec change were altered.

## Tests Before Behavior Change

- Characterize the existing `student` / `Workshop123!` login: HTTP 200, `user.username` is `student`, and `token` is present.
- Characterize current request validation and ordinary invalid credentials so this targeted security fix does not alter their response codes.
- Add one regression case per credential field using `' OR '1'='1`; each must assert HTTP 401 and absence of `token`. These assertions define the target behavior even though they fail before the fix.

## Risks / Trade-offs

- A parameter ordering or binding defect could reject valid users; the successful-login characterization detects that regression.
- The database currently converts lookup exceptions into no-match behavior. This design leaves that error-handling policy unchanged to avoid broadening the Issue's scope.
- Existing tests depend on the seeded workshop account. Run them from `auth/` as required by the repository workflow and avoid changing account fixtures as part of this fix.

## Rollback
