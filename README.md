Update the COBRA dependency logic.

Current behavior:
COBRA Event Code, COBRA Coverage Period, and COBRA Qualifying Event Date are enabled only when the "COBRA Qualifying Event" checkbox is checked.

Required behavior:
- If the "COBRA Qualifying Event" field is enabled (based on the dependency rules), then automatically enable:
  - COBRA Event Code
  - COBRA Coverage Period
  - COBRA Qualifying Event Date
- These fields should NOT depend on whether the checkbox is checked.
- They should only depend on whether the COBRA Qualifying Event field itself is enabled.
- If COBRA Qualifying Event becomes disabled, disable these three fields and clear their values.
- Do not modify any other dependency logic.
- Do not refactor existing code or change unrelated functionality.
