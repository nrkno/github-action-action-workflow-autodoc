# Github action for updating docs automaticly

A custom Github Action that can be used to automaticly populate docs from action/workflow definitions.

<!-- autodoc start -->
### Inputs

- `runs-on` (default `"['nrk-azure-intern', 'linux']"`, **required**) - The runner(s) to use for this workflow
- `workflow-file` (default `".github/workflows/plan.yaml"`, **required**) - Path to the workflow file to document
- `doc-file` (default `"README.md"`, **required**) - Path to the markdown file to update with documentation
- `start-token` (default `"<!-- autodoc start -->"`) - Token marking the start of the autodoc section
- `end-token` (default `"<!-- autodoc end -->"`) - Token marking the end of the autodoc section
- `commit-message` - Commit message to use when committing changes
- `author` - Author name to use for git commits
- `author-email` - Author email to use for git commits
- `debug` - Print debug messages
- `skip-commit` (default `"false"`) - Skip git add/commit/push and only update the doc file


### Required permissions

- `contents`: `read`
- `pull-requests`: `write`


### Example usage

#### Full example

```yaml
jobs:
  call-action:
    runs-on: <runs-on>
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Use action
        uses: <owner>/<repo>@<ref>
        with:
          runs-on: "['nrk-azure-intern', 'linux']"
          workflow-file: ".github/workflows/plan.yaml"
          doc-file: "README.md"
          start-token: "<!-- autodoc start -->"
          end-token: "<!-- autodoc end -->"
          commit-message: <commit-message>
          author: <author>
          author-email: <author-email>
          debug: <debug>
          skip-commit: "false"
```

#### Minimal example

```yaml
jobs:
  call-action:
    runs-on: <runs-on>
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Use action
        uses: <owner>/<repo>@<ref>
        with:
          runs-on: "['nrk-azure-intern', 'linux']"
          workflow-file: ".github/workflows/plan.yaml"
          doc-file: "README.md"
```
<!-- autodoc end -->"`) - Token marking the end of the autodoc section
- `commit-message` - Commit message to use when committing changes
- `author` - Author name to use for git commits
- `author-email` - Author email to use for git commits
- `debug` - Print debug messages
- `skip-commit` (default `"false"`) - Skip git add/commit/push and only update the doc file

### Required permissions

- `contents`: `read`
- `pull-requests`: `write`

### Example usage

#### Full example

```yaml
jobs:
  call-action:
    runs-on: <runs-on>
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Use action
        uses: <owner>/<repo>@<ref>
        with:
          runs-on: "['nrk-azure-intern', 'linux']"
          workflow-file: ".github/workflows/plan.yaml"
          doc-file: "README.md"
          start-token: "<!-- autodoc start -->"
          end-token: "<!-- autodoc end -->"
          commit-message: <commit-message>
          author: <author>
          author-email: <author-email>
          debug: <debug>
          skip-commit: "false"
```

#### Minimal example

```yaml
jobs:
  call-action:
    runs-on: <runs-on>
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Use action
        uses: <owner>/<repo>@<ref>
        with:
          runs-on: "['nrk-azure-intern', 'linux']"
          workflow-file: ".github/workflows/plan.yaml"
          doc-file: "README.md"
```

<!-- autodoc end -->

## Contributing

Create an issue and optionally a pull-request.
Use semantic commit messages.
