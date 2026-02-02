# Github action for updating docs automaticly

A custom Github Action that can be used to automaticly populate docs from action/workflow definitions.

<!-- start -->
## autodoc
Update readme with workflow and action docs.

### Required Inputs

|Input name|Description|Type|Default|
|---|---|---|---|
|**workflow_file**|Path to the workflow or action file to document<br>example workflow: `.github/workflows/plan.yaml`<br>example action: `action.yaml`<br>|string|`.github/workflows/plan.yaml`|
|**doc_file**|Path to the markdown file to update with documentation<br>example: README.md<br>|string|`README.md`|

### Optional Inputs

|Input name|Description|Type|Default|
|---|---|---|---|
|**start_token**|Token marking the start of the autodoc section<br>default value: <!-- autodoc start --><br>|string|`<!-- autodoc start -->`|
|**end_token**|Token marking the end of the autodoc section|string|`<!-- autodoc end -->`|
|**table**|Format inputs as a markdown table|string|`true`|
|**github-output**|Print documented inputs, secrets, and outputs to GitHub Action outputs|string|`false`|
|**debug**|Print debug messages. 0=none, 1=some, 2=more, 3=all|string|`0`|


### Outputs

|Output name|Description|
|---|---|
|autodoc_out|If enabled, the generated documentation for inputs, secrets, and outputs|

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
          table: true # Optional
          github-output: false # Optional
          debug: 0 # Optional
```


<!-- end -->

## Contributing

Create an issue and optionally a pull-request.
Use semantic commit messages.
