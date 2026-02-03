"""
Parses a GitHub Action or  reusable workflow file and creates usage notes in
Markdown format. Replaces the all content between `<!-- autodoc start -->` and
`<!-- autodoc end -->` within the `doc_file` with the generated documentation. Or you can set your own doc start and end tokens

stigok NRK June 2023
bateau84 NRK January 2026
"""
import configargparse
import difflib
import json
import os
import re
import subprocess
import sys
import textwrap
import uuid
import yaml

summary = ""

def debug_log(enabled, message, level=0):
    """Usage: call with the `--debug` flag to emit verbose trace statements."""
    if enabled >= level:
        if level == 1:
            print(f"[DEBUG] {message}")
        elif level == 2:
            print(f"[VERBOSE] {message}")
        elif level == 3:
            print(f"[GARBAGE] {message}")
        else:
          print(f"[INFO] {message}")

def determin_environment():
    """Determin if this is running in GitHub Actions or locally."""
    if "GITHUB_ACTIONS" in os.environ and os.environ["GITHUB_ACTIONS"] == "true":
        return "github"
    return "local"

def determin_workflow_or_action(workflow_content, debug):
    """Determine if the file is a GitHub Action or a reusable workflow."""
    if "on" in workflow_content:
        debug_log(debug, "Determined file type: workflow", 1)
        if "workflow_call" in workflow_content["on"]:
          return "workflow"
    elif "runs" in workflow_content:
        debug_log(debug, "Determined file type: action", 1)
        return "action"
    else:
        debug_log(debug, "Determined file type: unknown", 1)
        return "unknown"

def parse_workflow_file(workflow_file, debug):
    """Parse the workflow/action YAML file and return its content as a dict."""
    debug_log(debug, f"Parsing workflow file: {workflow_file}", 1)
    with open(workflow_file, "r", encoding="utf-8") as f:
        content = yaml.load(f, Loader=yaml.BaseLoader)
    debug_log(debug, f"Parsed content: {content}", 3)
    return content

def load_docs_file(doc_file, debug):
    """Load the documentation file to be updated."""
    debug_log(debug, f"Loading documentation file: {doc_file}", 1)
    with open(doc_file, "r", encoding="utf-8") as f:
        content = f.read()
    debug_log(debug, f"Loaded documentation content: {content}", 3)
    return content

def locate_docstring_section(docs_content, start_token, end_token, debug):
    """Locate the section in the docs file to be replaced."""
    debug_log(debug, f"Locating docstring section between '{start_token}' and '{end_token}'", 1)
    start_index = docs_content.find(start_token)
    end_index = docs_content.find(end_token, start_index)
    if start_index == -1 or end_index == -1:
        debug_log(debug, "Docstring section not found", 0)
        return None, None
    debug_log(debug, f"Located docstring section: start_index={start_index}, end_index={end_index}", 2)
    return start_index + len(start_token), end_index

def action_get_inputs(workflow_content, debug):
    """Extract inputs from a GitHub Action file."""
    debug_log(debug, "Extracting inputs from action", 1)
    all_inputs = {
        "inputs": {},
        "inputs_required": {}
    }
    if "inputs" in workflow_content:
        for input_name, input_props in workflow_content["inputs"].items():
            debug_log(debug, f"Processing input: {input_name} {input_props['required']}", 2)
            if "required" in input_props:
                input_props["required"] = str(input_props["required"]).lower()
                if input_props["required"] == "true":
                    all_inputs["inputs_required"][input_name] = input_props
                    continue
            all_inputs["inputs"][input_name] = input_props
    
    debug_log(debug, f"Found inputs: {len(all_inputs['inputs']) + len(all_inputs['inputs_required'])}", 0)
    add_to_summary(f"Found inputs: {len(all_inputs['inputs']) + len(all_inputs['inputs_required'])}")
    debug_log(debug, f"Found input: {all_inputs}", 3)
    return all_inputs

def action_get_outputs(workflow_content, debug):
    """Extract outputs from a GitHub Action file."""
    all_outputs = {}
    if "outputs" in workflow_content:
        for output_name, output_props in workflow_content["outputs"].items():
            debug_log(debug, f"Processing output: {output_name}", 2)
            all_outputs[output_name] = output_props
    debug_log(debug, f"Found outputs: {len(all_outputs)}", 0)
    add_to_summary(f"Found outputs: {len(all_outputs)}")
    debug_log(debug, f"Found outputs: {all_outputs}", 2)
    return all_outputs

def action_get_secrets(workflow_content, debug):
    """Extract secrets from a GitHub Action file."""
    all_secrets = {}
    if "secrets" in workflow_content:
        for secret_name, secret_props in workflow_content["secrets"].items():
            debug_log(debug, f"Processing secret: {secret_name}", 2)
            all_secrets[secret_name] = secret_props
    debug_log(debug, f"Found secrets: {len(all_secrets)}", 0)
    add_to_summary(f"Found secrets: {len(all_secrets)}")
    debug_log(debug, f"Found secrets: {all_secrets}", 2)
    return all_secrets

def workflow_get_inputs(workflow_content, debug):
    """Extract inputs from a reusable workflow file."""
    all_inputs = {
        "inputs": {},
        "inputs_required": {}
    }

    if "inputs" in workflow_content["on"]["workflow_call"]:
        for input_name, input_props in workflow_content["on"]["workflow_call"]["inputs"].items():
            debug_log(debug, f"Processing input: {input_name}", 2)
            if "required" in input_props and input_props["required"].lower() == "true":
                debug_log(debug, f"Input {input_name} is required", 2)
                input_props["required"] = str(input_props["required"]).lower()
                if input_props["required"] == "true":
                    all_inputs["inputs_required"][input_name] = input_props
            else:
                debug_log(debug, f"Input {input_name} is optional", 2)
                all_inputs["inputs"][input_name] = input_props
    debug_log(debug, f"Found inputs: {all_inputs}", 3)
    add_to_summary(f"Found inputs: {len(all_inputs['inputs']) + len(all_inputs['inputs_required'])}")
    debug_log(debug, f"Found inputs: {len(all_inputs['inputs']) + len(all_inputs['inputs_required'])}", 0)
    return all_inputs

def workflow_get_outputs(workflow_content, debug):
    """Extract outputs from a reusable workflow file."""
    all_outputs = {}
    
    if "outputs" in workflow_content["on"]["workflow_call"]:
        for output_name, output_props in workflow_content["on"]["workflow_call"]["outputs"].items():
            debug_log(debug, f"Processing output: {output_name}", 2)
            all_outputs[output_name] = output_props
    debug_log(debug, f"Found outputs: {all_outputs}", 2)
    add_to_summary(f"Found outputs: {len(all_outputs)}")
    debug_log(debug, f"Found outputs: {len(all_outputs)}", 0)
    return all_outputs

def workflow_get_secrets(workflow_content, debug):
    """Extract secrets from a reusable workflow file."""
    all_secrets = {}

    if "secrets" in workflow_content["on"]["workflow_call"]:
        for secret_name, secret_props in workflow_content["on"]["workflow_call"]["secrets"].items():
            debug_log(debug, f"Processing secret: {secret_name}", 2)
            all_secrets[secret_name] = secret_props
    debug_log(debug, f"Found secrets: {all_secrets}", 2)
    add_to_summary(f"Found secrets: {len(all_secrets)}")
    debug_log(debug, f"Found secrets: {len(all_secrets)}", 0)
    return all_secrets

def create_inputs_docstring(inputs, table, debug):
    """Create a Markdown docstring for inputs."""
    docstring = ""
    if len(inputs["inputs_required"]) > 0:
        if table:
          docstring = "### Required Inputs\n\n|Input name|Description|Type|Default|\n|---|---|---|---|\n"
        else:
          docstring = "### Required Inputs\n\n"
        
        for input_name, input_props in inputs["inputs_required"].items():
            if table:
              docstring += f"|**{input_name}**|{input_props.get('description', 'No description provided.').replace('\n', '<br>')}|{input_props.get('type', 'string')}|`{input_props.get('default', 'unknown')}`|\n"
            else:
              docstring += f"- **{input_name}**: {input_props.get('description', 'No description provided.').replace('\n', '   <br>')} (Default: `{input_props.get('default', 'None')}`, type: {input_props.get('type', 'string')})\n"
    if len(inputs["inputs"]) > 0:
        if table:
          docstring += "\n### Optional Inputs\n\n|Input name|Description|Type|Default|\n|---|---|---|---|\n"
        else:
          docstring += "\n### Optional Inputs\n\n"
        
        for input_name, input_props in inputs["inputs"].items():
            if table:
              docstring += f"|**{input_name}**|{input_props.get('description', 'No description provided.').replace('\n', '<br>')}|{input_props.get('type', 'string')}|`{input_props.get('default', 'None')}`|\n"
            else:
              docstring += f"- **{input_name}**: {input_props.get('description', 'No description provided.').replace('\n', '   <br>')} (Default: `{input_props.get('default', 'None')}`, type: {input_props.get('type', 'string')})\n"
    debug_log(debug, f"Created inputs docstring: \n{docstring}", 3)
    return docstring

def create_secrets_docstring(secrets, table, debug):
    """Create a Markdown docstring for secrets."""
    docstring = ""
    if len(secrets) > 0:
        if table:
          docstring = "### Secrets\n\n|Secret name|Description|Type|\n|---|---|---|\n"
        else:
          docstring += "### Secrets\n\n"
        
        for secret_name, secret_props in secrets.items():
            if table:
              docstring += f"|**{secret_name}**|{secret_props.get('description', 'No description provided.').replace('\n', '<br>')}|{secret_props.get('type', 'unknown')}|\n"
            else:
              docstring += f"- **{secret_name}**: {secret_props.get('description', 'No description provided.')} (type: {secret_props.get('type', 'unknown')})\n"
            
    debug_log(debug, f"Created secrets docstring: \n{docstring}", 3)
    return docstring

def create_outputs_docstring(outputs, table, debug):
    """Create a Markdown docstring for outputs."""
    docstring = ""
    if len(outputs) > 0:
        if table:
          docstring = "### Outputs\n\n|Output name|Description|\n|---|---|\n"
        else:
          docstring += "### Outputs\n\n"
        
        for output_name, output_props in outputs.items():
            if table:
              docstring += f"|{output_name}|{output_props.get('description', 'No description provided.').replace('\n', '<br>')}|\n"
            else:
              docstring += f"- **{output_name}**: {output_props.get('description', 'No description provided.')} (type: {output_props.get('type', 'unknown')})\n"
    debug_log(debug, f"Created outputs docstring: \n{docstring}", 3)
    return docstring

def create_action_examples_docstring(repo, branch, inputs, secrets, outputs, full, debug):
    """Create a Markdown docstring for examples."""
    example_template_jinja = textwrap.dedent("""\
    ### {full}
    
    ```yaml
    ---
    name: Example Workflow using this Action
    on:
      pull_request:

    jobs:
      example-job:
        name: Example Job
        steps:
          - uses: actions/checkout@v6
            with:
              ref: ${{ github.head_ref }}
              persist-credentials: true

          - name: example-step
            uses: {repo}@{branch}
            with:
    {inputs_section}
    
          - name: Commit and push changes
            uses: stefanzweifel/git-auto-commit-action@v7
            with:
              commit_message: "docs(autodoc): update documentation"
    ```
    """)
    inputs_section = ""
    for input_name, input_opts in inputs["inputs_required"].items():
        inputs_section += f"          {input_name}: {input_opts.get('default', '<value>')}\n"

    if full:
      for input_name, input_opts in inputs["inputs"].items():
          inputs_section += f"          {input_name}: {input_opts.get('default', '<value>')} # Optional\n"
    
    secrets_section = ""
    for secret_name in secrets:
        secrets_section += f"          {secret_name}: ${{{{ secrets.{secret_name} }}}}\n"
    
    outputs_section = ""
    for output_name in outputs:
        outputs_section += f"          {output_name}: ${{{{ steps.example_step.outputs.{output_name} }}}}\n"
    
    docstring = example_template_jinja.format(
        repo=repo,
        branch=branch,
        inputs_section=inputs_section.rstrip(),
        secrets_section=secrets_section.rstrip(),
        outputs_section=outputs_section.rstrip(),
        full="Full example usage" if full else "Simple example usage"
    )
    debug_log(debug, f"Created examples docstring: \n{docstring}", 3)
    return docstring

def create_workflow_examples_docstring(repo, workflow_file, branch, inputs, secrets, outputs, full, debug):
    """Create a Markdown docstring for examples."""
    example_template_jinja = textwrap.dedent("""\
    ### {full} (using steps 'uses' syntax)
    
    ```yaml
    ---
    name: workflow-example
    on:
      pull_request:

    jobs:
      example-job:
        steps:
          - name: example job
            id: example_step
            uses: {repo}/{workflow_file}@main{secrets_section}
            with:
    {inputs_section}
    ```
    """)
    inputs_section = ""
    for input_name, input_opts in inputs["inputs_required"].items():
        inputs_section += f"          {input_name}: '{input_opts.get('default', '<value>')}'\n"

    if full:
      for input_name, input_opts in inputs["inputs"].items():
          inputs_section += f"          {input_name}: '{input_opts.get('default', '<value>')}'\n"
    
    
    secrets_section = ""
    if full and len(secrets) > 0:
      secrets_section = "\n        secrets:\n"
      for secret_name in secrets:
          secrets_section += f"          {secret_name}: '${{{{ secrets.{secret_name} }}}}'\n"
    
    docstring = example_template_jinja.format(
        repo=repo,
        branch=branch,
        workflow_file=workflow_file,
        inputs_section=inputs_section.rstrip(),
        secrets_section=secrets_section.rstrip(),
        full="Full example usage" if full else "Simple example usage"
    )
    debug_log(debug, f"Created examples docstring: \n{docstring}", 3)
    return docstring

def is_newdocs_different(old_docs, new_docs):
    """Check if the new documentation content is different from the old."""
    test = difflib.ndiff(old_docs.splitlines(), new_docs.splitlines())
    debug_log(3, "\n".join(test), 3)

    # return old_docs != new_docs

def input_text_to_bool(input_text):
    """Convert various text representations of boolean to actual boolean."""
    if isinstance(input_text, bool):
        return input_text
    if input_text.lower() in ["true", "1", "yes", "on"]:
        return True
    return False

def set_github_output(name, value, file_type):
    """Sets a multiline GitHub Action output variable using a unique delimiter."""
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)
        print(f'input_type={file_type}', file=fh)

def add_to_summary(message):
    """Adds a message to the GitHub Action summary (not implemented)."""
    global summary
    summary += f"{message}\n"

def set_github_action_summary(summary_content):
    """Sets the GitHub Action summary (not implemented)."""
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
      f.write(summary_content)

if __name__ == "__main__":
    parser = configargparse.ArgParser(description=__doc__, add_env_var_help=True, auto_env_var_prefix="INPUT_")
    parser.add_argument(
        "--workflow-file",
        metavar="path/to/workflow.yaml",
        required=True,
        dest="workflow_file",
        help="Path to the workflow/action file (or set INPUT_WORKFLOW_FILE)",
    )
    parser.add_argument(
        "--doc-file",
        dest="doc_file",
        metavar="path/to/README.md",
        required=True,
        help="Path to the documentation file to update (or set INPUT_DOC_FILE)",
    )
    parser.add_argument(
        "--start-token",
        dest="start_token",
        default="<!-- autodoc start -->",
        required=False,
        help="Marker indicating where autogenerated docs start",
    )
    parser.add_argument(
        "--end-token",
        dest="end_token",
        default="<!-- autodoc end -->",
        required=False,
        help="Marker indicating where autogenerated docs end",
    )
    parser.add_argument(
        "--table",
        dest="table",
        default="False",
        required=False,
        help="Output inputs, secrets, and outputs as markdown tables",
    )
    parser.add_argument(
        "--working-directory",
        dest="working_directory",
        default=None,
        required=False,
        help="Set the working directory for git operations",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        metavar="LEVEL",
        default="0",
        required=False,
        help="Enable verbose logging, leve 1 to 3",
    )
    
    args = parser.parse_args()

    if args.debug == False or args.debug.lower() == "false":
        args.debug = 0
    elif args.debug == True or args.debug.lower() == "true":
        args.debug = 2
    else:
        try:
            args.debug = int(args.debug)
        except ValueError:
            args.debug = 0
    
    args.table = input_text_to_bool(args.table)

    for test in args.__dict__:
        debug_log(args.debug, f"Argument {test} = \"{args.__dict__[test]}\"", 1)
    
    env = determin_environment()
    debug_log(args.debug, f"Running in {env} environment", 1)

    workflow_content = parse_workflow_file(args.workflow_file, args.debug)
    docs_file = load_docs_file(args.doc_file, args.debug)
    docs_path = os.path.dirname(os.path.abspath(args.doc_file))
    file_type = determin_workflow_or_action(workflow_content, args.debug)
    script_path = os.path.dirname(os.path.abspath(__file__))

    if env == "github":
        github_repo = os.environ.get("GITHUB_REPOSITORY", None)
        # github_branch = os.environ.get("GITHUB_HEAD_REF", None)
        github_branch = os.environ.get("GITHUB_REF", None)
        github_sha = os.environ.get("GITHUB_SHA", None)
        github_event_type = os.environ.get("GITHUB_EVENT_NAME", None)
        working_dir = args.working_directory or os.environ.get("GITHUB_WORKSPACE", None)

        if file_type == "action":
            workflow_path = os.path.dirname(os.path.abspath(args.workflow_file))
        else:
          workflow_path = os.path.dirname(os.path.abspath(os.path.join(args.workflow_file, "../..")))
        
    else:
        github_repo_url = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True).stdout.strip()
        github_repo = re.sub(r"^(?:.*github.com)(?:\/|:)(.*)(?:\.git)$", r"\1", github_repo_url)
        github_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
        github_event_type = "local-testing"

        if file_type == "action":
            workflow_path = os.path.dirname(os.path.abspath(args.workflow_file))
        else:
          workflow_path = os.path.dirname(os.path.abspath(os.path.join(args.workflow_file, "../..")))
        
        if workflow_path == docs_path:
          working_dir = workflow_path
        else:
          working_dir = docs_path
        
    debug_log(args.debug, f"GitHub repo = {github_repo}", 0)
    debug_log(args.debug, f"GitHub branch = {github_branch}", 0)
    debug_log(args.debug, f"GitHub event type = {github_event_type}", 1)
    
    debug_log(args.debug, f"script path = {script_path}", 1)
    debug_log(args.debug, f"docs directory = {docs_path}", 0)
    debug_log(args.debug, f"{file_type} directory = {workflow_path}", 0)
    debug_log(args.debug, f"Working directory = {working_dir}", 1)

    match file_type:
        case "action":
            name = workflow_content.get("name", "")
            description = workflow_content.get("description", "")
            inputs = action_get_inputs(workflow_content, args.debug)
            secrets = action_get_secrets(workflow_content, args.debug)
            outputs = action_get_outputs(workflow_content, args.debug)
            full_example_docstring = create_action_examples_docstring(github_repo, "v2", inputs, secrets, outputs, True, args.debug)
            simple_example_docstring = create_action_examples_docstring(github_repo, "v2", inputs, secrets, outputs, False, args.debug)
        case "workflow":
            name = workflow_content.get("name", "")
            description = workflow_content.get("description", "")
            inputs = workflow_get_inputs(workflow_content, args.debug)
            secrets = workflow_get_secrets(workflow_content, args.debug)
            outputs = workflow_get_outputs(workflow_content, args.debug)
            full_example_docstring = create_workflow_examples_docstring(github_repo, args.workflow_file, "v2", inputs, secrets, outputs, True, args.debug)
            simple_example_docstring = create_workflow_examples_docstring(github_repo, args.workflow_file, "v2", inputs, secrets, outputs, False, args.debug)
        case _:
            print(f"[ERROR] Unable to determine if file is a GitHub Action or reusable workflow: {args.workflow_file}")
            sys.exit(1)

    debug_log(args.debug, f"{file_type} name: {name}", 1)
    debug_log(args.debug, f"{file_type} description: {description}", 1)
    debug_log(args.debug, f"{file_type} inputs: {inputs}", 2)
    debug_log(args.debug, f"{file_type} secrets: {secrets}", 2)
    debug_log(args.debug, f"{file_type} outputs: {outputs}", 2)

    add_to_summary(f"GitHub repo = {github_repo}")
    add_to_summary(f"GitHub branch = {github_branch}")
    add_to_summary(f"GitHub event type = {github_event_type}")
    add_to_summary(f"File type = {file_type}")
    add_to_summary(f"{file_type.capitalize()} name = {name}")

    inputs_docstring = create_inputs_docstring(inputs, args.table, args.debug)
    secrets_docstring = create_secrets_docstring(secrets, args.table, args.debug)
    outputs_docstring = create_outputs_docstring(outputs, args.table, args.debug)
    
    created_docstring = f"""\
## {name or 'Unnamed ' + file_type.capitalize()}
{description}
{inputs_docstring}
{secrets_docstring}
{outputs_docstring}
{simple_example_docstring}
{full_example_docstring}
"""
    
    if env == "github":
        set_github_output("autodoc_out", created_docstring, file_type)
        set_github_action_summary(summary)
    elif env == "local":
        print("Summary of findings:")
        print(summary)

    start_index, end_index = locate_docstring_section(docs_file, args.start_token, args.end_token, args.debug)
    if start_index is None or end_index is None:
        print(f"[ERROR] Could not find docstring section in {args.doc_file} between '{args.start_token}' and '{args.end_token}'")
        sys.exit(1)

    new_docs_content = docs_file[:start_index] + "\n" + created_docstring + "\n" + docs_file[end_index:]
    debug_log(args.debug, f"Generated new documentation content: \n{new_docs_content}", 3)
    
    if new_docs_content != docs_file:
        debug_log(args.debug, "Documentation content has changed, updating file.", 0)
        try:
          with open(args.doc_file, "w", encoding="utf-8") as f:
              f.write(new_docs_content)

          sys.exit(0)
        except Exception as e:
          print(f"[ERROR] Failed to write updated documentation to {args.doc_file}: {e}")
          sys.exit(1)

    else:
        debug_log(args.debug, "No changes detected in documentation content. No update needed.", 1)
        sys.exit(0)