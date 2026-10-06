# Regression: narrative shape routing must not over-apply expert-blog style

## Defect

Fixing the expert-blog case can create a new regression if the Skill starts writing every note as a thesis-driven article or forces bilingual output everywhere.

## Case A: troubleshooting note

Input:
- a personal debugging note with one error message, three attempted fixes, one confirmed fix, and one unresolved question;
- no request for a blog or public article;
- no request for bilingual output.

Expected:
- keep troubleshooting shape;
- preserve first-person experience where it is genuinely the author's experience;
- organize around symptom, attempts, confirmed result, and unresolved gap;
- do not invent a central industry thesis;
- do not add English.

## Case B: technical lecture requested as Chinese expert blog

Input:
- a technical lecture transcript;
- explicit request for an expert blog;
- Chinese only.

Expected:
- use the expert-article shape;
- choose one supported thesis and use the lecture as evidence;
- do not default to first person;
- use short concept/mechanism headings;
- keep Chinese only.

## Case C: the same lecture requested as compact bilingual expert blog

Expected:
- keep the same thesis and evidence discipline as Case B;
- heading format: `中文 | English`;
- body format: complete Chinese paragraph immediately followed by equivalent English in the same paragraph;
- no separate Chinese section and English section;
- no information loss or certainty drift in translation.

## Generalization check

Output shape follows the user's intended use and source type. Expert-blog style is opt-in, not a new universal default.
