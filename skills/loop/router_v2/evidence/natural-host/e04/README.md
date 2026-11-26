## GitHub adapter and E04/E05

The trusted host supplies a grant pinning the repository, isolated branch, path, expected head, operation ID and exact UTF-8 bytes. Supplying the same fields in a task cannot authorize a write. The host also supplies a trusted Git-object reader for the tree of that immutable expected head.

The adapter creates an ordinary file tree and a single-parent commit, then moves the branch with a non-forced, expected-head update. A staging failure can leave unreachable Git objects. Recovery reads the current branch head and checks its operation marker, direct ancestry distance, exact one-file diff and exact file bytes. A different current head blocks. Automatic history search and branch deletion/recreation by an administrator are outside this contract. The enabled file mode is 100644.

The independent checker fetches the branch into a fresh temporary Git repository, checks its complete parent list, changed paths and bytes, then executes the downloaded module against empty and mixed-sign inputs. Run E04 before E05 advances the same branch. Immutable commits can also be inspected through GitHub.

The evidence in each case separates provider requests from the Legion journal and validation result. Fault injection in E05 discards the write receipt after remote confirmation, then stops the host after its unknown-outcome checkpoint has been saved. A fresh host reads the same checkpoint and reconciles using read-only connector operations.
