# PDF form integration — 18 November 2026 fields

`pdf_form.py` reads Sportsbet/Punters meeting PDFs with `pdftotext -layout`
(Poppler is required). It returns race cards, identified runner blocks,
parsed historical starts and quarantined ambiguous rows. Run after adding
`monty_v6` to the import path, as established by `import race_day`.

`match_start` requires date, documented track-code mapping, distance, runner
name, full retained field size, outcome and a unique historical market row.
The historical market must have one winner and valid scheduled-off back
quotes. Printed SP is extracted as source metadata but never used as a V6
historical probability. An unmapped track code or ambiguous identity is not
resolved by guessing.

Fitness/distance-change features can be added only when the latest actual
PDF race matches a retained market, there is no quarantined row for that
runner, and no later canonical start under the matched selection ID exists.
The formulas reproduce the original builder. Do not use a later actual
start when retained-market eligibility is unverified. Current connections
are full names and historic names may be abbreviated; changes are not
inferred from string differences.

Five real guides yielded 423 active runner blocks, 1,451 parsed race starts,
375 matched historical starts and 103 runners with
verified latest starts. Seven possible features are recovered: three
recency, three distance-change and benchmark-class change where both classes
are numeric. Active input counts range 13–21/43; this is still incomplete.

Cumulative horse histories, market residuals, connections residuals and
jockey/trainer changes remain missing. The October source does not cover
recent November starts or complete histories. No invented zero histories,
career-rate substitutions or training changes are made.

The rerun retained the 17 November 14:19 Queensland advance odds. Sandown R3
prices form an underround after removal of scratched Fammi and cannot
support actionable positive-edge claims. Track going still needs current
verification. Timaru has no PDF in this run. Raw third-party PDFs, parsed
histories, source identities and runner outputs remain private; only code,
synthetic tests and aggregate counts are published.

Validation: `python -m unittest test_pdf_form -v`. Original artifacts and
their 55-entry manifest remain unchanged.
