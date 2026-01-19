# Github action for updating docs automaticly

A custom Github Action that can be used to automaticly populate docs from action/workflow definitions.

<!-- start -->
## autodoc
Update readme with workflow and action docs.

### Required Inputs

- **workflow_file**: Path to the workflow file to document (type: unknown)
- **doc_file**: Path to the markdown file to update with documentation (type: unknown)

### Optional Inputs

- **start_token**: Token marking the start of the autodoc section (Default: "<!-- autodoc start -->", type: unknown)
- **end_token**: Token marking the end of the autodoc section (Default: "<!-- autodoc end -->", type: unknown)
- **commit_message**: Commit message to use when committing changes (Default: "None", type: unknown)
- **author**: Author name to use for git commits (Default: "None", type: unknown)
- **author_email**: Author email to use for git commits (Default: "None", type: unknown)
- **debug**: Print debug messages. 0=none, 1=some, 2=more, 3=all (Default: "0", type: unknown)
- **skip_commit**: Skip git add/commit/push and only update the doc file (Default: "false", type: unknown)



### Simple example usage

```yaml
---
name: Example Workflow using this Action
on:
  pull_request:

jobs:
  example-job:
    name: Example Job
    steps:
      - uses: actions/checkout@v3

      - name: example-step
        uses: nrkno/github-action-action-workflow-autodoc@v1
        with:
          workflow_file: .github/workflows/plan.yaml
          doc_file: README.md
```

### Full example usage

```yaml
---
name: Example Workflow using this Action
on:
  pull_request:

jobs:
  example-job:
    name: Example Job
    steps:
      - uses: actions/checkout@v3

      - name: example-step
        uses: nrkno/github-action-action-workflow-autodoc@v1
        with:
          workflow_file: .github/workflows/plan.yaml
          doc_file: README.md
          start_token: <!-- autodoc start --> # Optional
          end_token: <!-- autodoc end --> # Optional
          commit_message: <value> # Optional
          author: <value> # Optional
          author_email: <value> # Optional
          debug: 0 # Optional
          skip_commit: false # Optional
```


<!-- end -->

## Contributing

Create an issue and optionally a pull-request.
Use semantic commit messages.
