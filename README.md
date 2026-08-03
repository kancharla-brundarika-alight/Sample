Task:
Implement the field dependency logic for the Dependent/COBRA & HIPAA Events module based on the dependency sheet.

Important Constraints:
- Do NOT refactor existing code.
- Do NOT change APIs, models, database schema, routing, or component structure.
- Do NOT modify unrelated functionality.
- Keep all existing validations and business logic intact.
- Only implement the dependency rules.
- Reuse existing state management, validation framework, and event handlers.
- If a dependency already exists, extend it instead of replacing it.
- Keep backward compatibility.
- Do not introduce duplicate logic.
- Add comments only where new dependency logic is introduced.

Dependency Rules

1. Employer Event
- enable -> field is editable.
- disable -> field is disabled and its value should be cleared.
- N/A -> field remains hidden/disabled as per existing implementation.

2. Forced Window Close
- If value is
    "depends on Employer (if employer checked Force Window Close)"
  then
    - Read the Employer level "Force Window Close" setting.
    - Enable only when Employer Force Window Close is checked.
    - Otherwise disable and clear the value.

3. COBRA Qualifying Event
- If dependency is
    "depends on Employer (if employer checked COBRA Qualifying Event)"
  then
    - Read Employer COBRA Qualifying Event setting.
    - Enable only when Employer setting is enabled.
    - Otherwise disable and clear.

4. COBRA Event Code
- Enable only if
    COBRA Qualifying Event == checked
- Otherwise
    disable and clear.

5. COBRA Coverage Period
- Enable only if
    COBRA Qualifying Event == checked
- Otherwise
    disable and clear.

6. COBRA Qualifying Event Date
- Enable only if
    COBRA Qualifying Event == checked
- Otherwise
    disable and clear.

7. LOA Child Events
For every LOA child event:
- Military Leave
- Illness
- Disability
- Child Birth/Adoption
- Education
- FMLA
- MLOA
- Layoff
- Internship
- Personal
- On the Job Injury
- Company Convenience Leave
- Voluntary Leave
- Union Leave
- Maternity Leave
- Parental Leave
- All Other Reasons

Rule:
If parent LOA event is enabled
    -> child becomes enabled.
Else
    -> child remains disabled.

8. Disable Behaviour
Whenever a field becomes disabled because of dependency:
- Clear its current value.
- Remove validation errors.
- Remove touched state if applicable.
- Do not submit stale values.

9. Initial Load
When the screen loads:
- Evaluate all dependencies.
- Populate enabled/disabled state correctly from existing data.

10. Runtime Updates
Whenever any parent field changes:
- Recalculate all dependent fields immediately.
- No page refresh.
- No manual save required.

11. Existing Data
If existing saved data violates the dependency:
- Disable the child.
- Clear invalid value.
- Keep parent data untouched.

Implementation Guidelines
- Use existing dependency utilities if available.
- Avoid hardcoding logic in UI components.
- Prefer centralized dependency evaluation.
- Keep logic modular.
- Avoid duplicate conditions.
- Preserve current styling.
- Preserve existing API payload structure.
- Preserve existing response handling.
- Do not modify unrelated files.

Acceptance Criteria
✓ All dependencies from the dependency sheet work.
✓ Employer settings drive dependent fields correctly.
✓ COBRA fields enable only after COBRA Qualifying Event is checked.



Implement ONLY the COBRA dependency changes listed below. Do NOT modify any other event or existing functionality.

Important:
- Do NOT refactor the code.
- Do NOT change API contracts, models, database schema, routing, or UI layout.
- Preserve all existing functionality.
- Implement the dependency only for the rows listed below.
- If a dependency already exists, extend it instead of replacing it.
- Keep all existing validations.
- Do not touch events not mentioned below.

For every row below:

Rule 1:
If Employer-level "COBRA Qualifying Event" is enabled,
enable the event-level "COBRA Qualifying Event" checkbox.

Otherwise:
- Disable it.
- Clear its value.

Rule 2:
If Event-level "COBRA Qualifying Event" is checked,
then enable:
- COBRA Event Code
- COBRA Coverage Period (Months)
- COBRA Qualifying Event Date

Otherwise:
- Disable all three fields.
- Clear their values.
- Remove validation errors if applicable.

Apply this ONLY to the following rows:

Employment Events
---------------
Row 16 - Employee Termination (Layoff)
Row 17 - Employee Termination (Severance Continuation)
Row 18 - Employee Termination (Death of Employee)

Employment Changes
------------------
Row 40 - Loss of Eligibility Due to Retirement
Row 44 - Reduction in Work Hours
Row 47 - Loss of Plan Eligibility (Retiree Health)
Row 49 - Loss of Plan Eligibility (Employer Mandate)

Life Status Change
------------------
Row 56 - Divorce
Row 57 - Legal Separation
Row 59 - Loss of Domestic Partnership

Batch Events
------------
Row 72 - Loss of Dependent Eligibility
Row 73 - Dependent Aging Out
Row 75 - Full-time Student Denied from Coverage

The following rows have COBRA enabled directly (no Employer dependency). When the COBRA Qualifying Event checkbox is checked, enable the dependent COBRA fields:

Employment Events
-----------------
Row 7  - Employee Termination (Resignation)
Row 8  - Employee Termination (Involuntary Termination)
Row 9  - Employee Termination (Medicare / Retirement / Termination)
Row 10 - Employee Termination (Gross Misconduct)
Row 11 - Employee Termination (Military)
Row 12 - Employee Termination (Loss After Chapter 11 Bankruptcy)
Row 13 - Employee Termination (COBRA +11 Month Disability Extension)
Row 14 - Employee Termination (COBRA +13 Month Disability Extension)

Do NOT enable COBRA fields for any other rows.
Rows marked as "disable" in the dependency sheet must remain disabled.
Do not modify any unrelated code or existing business logic.
✓ Force Window Close dependency works.
✓ LOA parent-child dependency works.
✓ Disabled fields are cleared.
✓ Existing functionality remains unchanged.
✓ No regression in other screens.
✓ No unnecessary code changes outside dependency implementation.
