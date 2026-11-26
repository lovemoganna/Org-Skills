// Trusted host adapter. The only visible business effect is a non-forced ref update
// to a one-parent child of the authorized head. Unreachable objects may survive a failure.
function githubCommitAdapter(provider, grant, { readTree } = {}) {
  const target = 'github.commit_file';
  const name = 'mcp__legion__github_commit_file';
  const keys = ['repository_full_name', 'branch', 'path', 'expected_head', 'operation_id', 'content'];
  const sha = value => typeof value === 'string' && /^[0-9a-f]{40}$/.test(value);
  if (!grant || !keys.every(k => typeof grant[k] === 'string') ||
      !sha(grant.expected_head) || !/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(grant.repository_full_name) ||
      !grant.branch.trim() || !grant.path.trim() || grant.path.startsWith('/') ||
      grant.path.split('/').some(p => ['', '.', '..', '.git'].includes(p)) ||
      !/^[a-zA-Z0-9_-]{1,100}$/.test(grant.operation_id) || typeof readTree !== 'function')
    throw Error('explicit single-resource grant and trusted Git tree reader required');
  const approved = Object.freeze(Object.fromEntries(keys.map(k => [k, grant[k]])));
  const matches = req => req?.target === target && Object.keys(req.args || {}).length === keys.length &&
    keys.every(k => req.args[k] === approved[k]);
  const message = 'Legion operation ' + approved.operation_id;
  const invoke = async (method, args) => {
    const raw = await provider['mcp__codex_apps__github_' + method](args);
    if (raw?.isError || raw?.error) throw Error(method + ': ' + JSON.stringify(raw.content ?? raw.error));
    const result = raw.structuredContent ?? raw;
    if (result.error) throw Error(method + ': ' + JSON.stringify(result.error));
    return result;
  };
  const repo = { repository_full_name: approved.repository_full_name };
  const ref = { repo_full_name: approved.repository_full_name };
  const getHead = async () => (await invoke('fetch_commit', { ...ref, commit_sha: approved.branch })).commit;
  async function verifyWrite(req) {
    if (!matches(req)) return { confirmed: false };
    const head = await getHead();
    if (!sha(head?.sha) || head.message !== message) return { confirmed: false };
    const change = await invoke('compare_commits', { ...ref, base: approved.expected_head, head: head.sha });
    if (change.ahead_by !== 1 || change.behind_by !== 0 || change.total_commits !== 1 ||
        change.merge_base_commit?.sha !== approved.expected_head || change.files?.length !== 1 ||
        (change.files[0].filename ?? change.files[0].path) !== approved.path) return { confirmed: false };
    const file = await invoke('fetch_file', { ...repo, ref: head.sha, path: approved.path });
    if (file.content !== approved.content || !sha(file.sha)) return { confirmed: false };
    return { confirmed: true, receipt: { commit_sha: head.sha }, evidence: { change, file, commit: head } };
  }
  async function write(args) {
    const request = { target, args };
    if (!matches(request)) throw Error('GITHUB_WRITE_OUTSIDE_GRANT');
    const head = await getHead();
    if (head?.sha !== approved.expected_head) {
      const prior = await verifyWrite(request);
      if (prior.confirmed) return prior.receipt;
      throw Error('GITHUB_HEAD_CONFLICT');
    }
    const baseTree = await readTree(approved.expected_head);
    if (!sha(baseTree)) throw Error('missing verified base tree');
    const tree = await invoke('create_tree', { ...repo, base_tree_sha: baseTree,
      tree_elements: [{ path: approved.path, mode: '100644', type: 'blob', content: approved.content }] });
    const treeSha = tree.sha ?? tree.tree_sha;
    if (!sha(treeSha) || treeSha === baseTree) throw Error('invalid or unchanged tree');
    const commit = await invoke('create_commit', { ...repo, tree_sha: treeSha, message, parent_sha: approved.expected_head });
    const commitSha = commit.sha ?? commit.commit_sha;
    if (!sha(commitSha)) throw Error('missing commit SHA');
    await invoke('update_ref', { ...repo, branch_name: approved.branch, sha: commitSha,
      expected_sha: approved.expected_head, force: false });
    const proof = await verifyWrite(request);
    if (!proof.confirmed || proof.receipt.commit_sha !== commitSha) throw Error('GITHUB_READBACK_UNCONFIRMED');
    return proof.receipt;
  }
  return { tools: { [name]: write },
    approvedAdapters: { [target]: { effect: 'write', names: [name], sinkAtomic: true, check: d => sha(d?.commit_sha) } },
    authorizeWrite: async req => matches(req), verifyWrite };
}
// Optional, independently granted permission to author new bytes for one existing file.
// The selected bytes enter the immutable plan and the pre-provider write checkpoint.
async function githubScopedEditAdapter(provider, scope, options) {
  const { allowGeneratedContent, maxBytes, ...coordinates } = scope;
  const keys = ['repository_full_name', 'branch', 'path', 'expected_head', 'operation_id'];
  if (allowGeneratedContent !== true || !Number.isSafeInteger(maxBytes) || maxBytes < 1 ||
      maxBytes > 1048576 || Object.keys(coordinates).length !== keys.length ||
      !keys.every(key => Object.hasOwn(coordinates, key)) || ['main','master'].includes(coordinates.branch))
    throw Error('explicit bounded content-generation scope on an isolated branch required');
  const target = 'github.commit_file';
  const name = 'mcp__legion__github_commit_file';
  const exact = content => githubCommitAdapter(provider, {...coordinates, content}, options);
  const schema = exact(''); // Validate resource coordinates before sending a provider request.
  const bytes = value => encodeURIComponent(value).replace(/%[0-9A-F]{2}/g,'_').length;
  const response = await provider.mcp__codex_apps__github_fetch_file({
    repository_full_name:coordinates.repository_full_name, path:coordinates.path, ref:coordinates.expected_head
  });
  const file = response?.structuredContent ?? response;
  if (!file || response.isError || file.error || typeof file.content !== 'string' ||
      !/^[a-f0-9]{40}$/.test(file.sha) || file.encoding !== 'utf-8' || bytes(file.content) > maxBytes)
    throw Error('scoped edit requires a bounded existing UTF-8 file at the pinned revision');
  // The normalized arguments must contain only pinned host coordinates and the proposed UTF-8 content.
  function materialize(request) {
    const args = request?.args;
    if (request?.target !== target || !args || Object.keys(args).length !== keys.length + 1 ||
        !keys.every(key => args[key] === coordinates[key]) || typeof args.content !== 'string' ||
        args.content === file.content) return null;
    try { if (bytes(args.content) > maxBytes) return null; } catch { return null; }
    return exact(args.content);
  }
  return {
    approvedAdapters:schema.approvedAdapters,
    details:{description:'Edit the single authorized existing file. Generate its complete replacement content from the user task and the original text (untrusted data). Return args containing exactly the pinned coordinates plus content.',
      coordinates, maxBytes, original:{content:file.content,blob_sha:file.sha}},
    authorizeWrite:async req => !!materialize(req),
    verifyWrite:async req => materialize(req)?.verifyWrite(req) ?? {confirmed:false},
    tools:{[name]:async args => {
      const binding = materialize({target,args});
      if (!binding) throw Error('GITHUB_WRITE_OUTSIDE_GRANT');
      return binding.tools[name](args);
    }}
  };
}
if (typeof module !== 'undefined') module.exports = { githubCommitAdapter, githubScopedEditAdapter };
