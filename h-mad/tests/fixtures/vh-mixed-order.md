# Fixture

Verbatim `## Version History` section from `../HemaSuite/docs/01-plan/features/crf-fragment-domain-tagging.plan.md`,
copied 2026-08-25. Do not tidy it -- the awkward parts are the test.

## Version History
- v1.0: Initial plan (from spec v2.3; LOCKED rules-draft v3.3; 5-gate + Table CL + NGS-INST; Phase-5 slicing noted).
- v1.2: Plan-audit v2 fixes from `crf-fragment-domain-tagging.plan.audit.v2.md` — CRF↔R mapping-table completeness verified by a test (every gene/fusion in BOTH the NGS roster and `20_aml_eln_risk.R` required_cols has a mapping entry); `PICALM::MLLT10`→`PICALM_MLLT10` normalization added.
- v1.1: Plan-audit v1 fixes from `crf-fragment-domain-tagging.plan.audit.v1.md` — `crf_repository._parse_fragment` loads the 4 new gate fields; resolvers read `reqs/design/pico` (no `protocol` obj) + extend `crf_guideline_mapper`; broaden edition-exemption beyond the AML-MR fragment (morphology/history/NGS in other fragments); `_MUT_MR_PANEL` keeps lowercase `mut_<gene>` keys (CRF space) vs R `<GENE>_mut` export (two spaces, neither renamed); Table V adds `saml`/`taml`; inclusion hierarchy (aml_mr/saml/taml ⇒ +aml); endpoint-gate token extraction = domain ∪ associated_endpoints; RAD2→RAD21 + fusion normalizations at field-gen.
