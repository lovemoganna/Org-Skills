# Regression: polished source must produce knowledge gain without bloat

## Defect

A polished tutorial can already be clear, accurate, and well structured. The previous Skill could preserve that structure and still produce a weak next version: headings change, paragraphs compress, but the latent mechanism and reusable decision rules remain implicit.

Reusable root cause: "preserve a good structure" was not paired with a strong enough requirement to extract relationships, mechanisms, decision boundaries, and failure conditions.

## Source used for the real-world test

MDN, "How to use promises":
https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Async_JS/Promises

The test uses these source facts:

- a Promise represents an asynchronous operation that can be pending, fulfilled, or rejected;
- promise chaining is used when later asynchronous work depends on earlier results;
- `catch()` at the end of a chain can receive failures from preceding asynchronous steps;
- `fetch()` can fulfill even when the HTTP response is an error such as 404, so code checks `response.ok`;
- `Promise.all()` is useful when all independent operations are required;
- `Promise.any()` is useful when any one successful result is enough;
- `async`/`await` uses Promise semantics; sequential `await` can serialize operations that do not depend on each other.

## Expected behavior

The reforge must preserve the source facts and executable examples, but it must not stop at a cleaner tutorial.

It should surface at least these reusable relationships when supported by the source:

- dependency determines sequencing: dependent operations are chained/awaited in order; independent operations should not be serialized without a reason;
- transport/Promise failure and HTTP application status are different layers: a 404 response can still be a fulfilled fetch, so HTTP success needs an explicit `response.ok` check;
- `async`/`await` changes expression style, not the underlying Promise dependency model;
- the choice between a chain/`await`, `Promise.all()`, and `Promise.any()` follows the dependency and completion requirement, not syntax preference.

These can be expressed compactly. They do not require new named frameworks or a larger document.

Any additional mechanism or judgment that is not directly supported by the source must be omitted or marked according to the Skill's `〔补〕` rule.

## Failure conditions

Fail if the output:

- only paraphrases or rearranges the tutorial;
- says `fetch()` rejects merely because the server returns 404;
- says `await` blocks the whole program;
- turns "async/await is intuitive" into a universal rule to always prefer it;
- invents performance numbers or runtime guarantees;
- expands the internal 三魂七魄 model into ten user-facing sections;
- becomes materially longer without new decision value.

## Generalization check

The same behavior must apply to any already-polished concept note, tutorial, article-derived note, or documentation note: preserve what is already good, then look for latent relationships and decision boundaries before deciding whether any rewrite is needed.
