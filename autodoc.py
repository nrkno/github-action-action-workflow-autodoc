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

import yaml


def debug_log(enabled, message):
    """Usage: call with the `--debug` flag to emit verbose trace statements."""
    if enabled:
        print(f"[autodoc] {message}")


def detect_repo_info(workflow_path, debug=False):
    """Usage: call with a workflow path to resolve git metadata and refs for docs."""

    def run_git(args_list, cwd):
        try:
            return subprocess.check_output(
                ["git", *args_list],
                cwd=cwd,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    workflow_dir = os.path.dirname(workflow_path)
    repo_root = run_git(["rev-parse", "--show-toplevel"], workflow_dir)

    owner = repo = ref = None
    if repo_root:
        remote = run_git(["config", "--get", "remote.origin.url"], repo_root)
        if remote:
            if remote.endswith(".git"):
                remote = remote[:-4]
            if remote.startswith("git@github.com:"):
                owner_repo = remote.split(":", 1)[1]
            elif remote.startswith("https://github.com/"):
                owner_repo = remote.split("github.com/", 1)[1]
            else:
                owner_repo = None
            if owner_repo and "/" in owner_repo:
                owner, repo = owner_repo.split("/", 1)

        ref = run_git(["describe", "--tags", "--abbrev=0"], repo_root)
        if not ref:
            ref = run_git(["rev-parse", "--short", "HEAD"], repo_root)
    else:
        ref = None

    rel_path = os.path.relpath(workflow_path, repo_root) if repo_root else os.path.relpath(workflow_path)
    rel_path = rel_path.replace(os.sep, "/")

    if owner and repo and ref:
        workflow_ref = f"{owner}/{repo}/{rel_path}@{ref}"
        action_ref = f"{owner}/{repo}@{ref}"
    else:
        workflow_ref = f"<owner>/<repo>/{rel_path}@<ref>"
        action_ref = f"<owner>/<repo>@<ref>"

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root) if repo_root else None
    debug_log(debug, f"Resolved workflow ref '{workflow_ref}' and branch '{branch or 'HEAD'}'.")

    return {
        "repo_root": repo_root,
        "workflow_ref": workflow_ref,
        "action_ref": action_ref,
        "branch": branch or "HEAD",
    }


def document_workflow_arg(
    *,
    name,
    type=None,
    default=None,
    required=None,
    description=None,
    value=None,
):
    """
    Usage: call to convert a workflow/action input definition into a Markdown bullet.
    >>> print(document_workflow_arg(name="foo"))
    - `foo`
    >>> print(document_workflow_arg(name="foo", default=True))
    - `foo` (default `true`)
    >>> print(document_workflow_arg(name="foo", required=True))
    - `foo` (**required**)
    >>> print(document_workflow_arg(name="foo", description="hello"))
    - `foo` - hello
    >>> print(document_workflow_arg(name="foo", type="string", default="bar", required=True, description="hello"))
    - `foo` (string, default `"bar"`, **required**) - hello
    >>> print(document_workflow_arg(name="foo", description="hello", value="something"))
    - `foo` - hello
    """
    props = []
    if type:
        props.append(type)
    if default is not None:
        props.append(f"default `{json.dumps(default)}`")
    if required:
        props.append("**required**")

    s = f"- `{name}`"
    if props:
        s += " ("
        s += ", ".join(props)
        s += ")"

    if description:
        description, _ = extract_autodoc_metadata(description)
        s += " - "
        s += description

    return s

def _get_on_section(workflow_def):
    """Usage: call with a workflow dict to safely access its `on` section."""
    if "on" in workflow_def:
        return workflow_def["on"]
    # PyYAML 1.1 treats the word "on" as boolean True unless YAML 1.2 mode is used.
    if True in workflow_def:
        return workflow_def[True]
    return {}

def workflow_or_action(workflow_def):
    """
    Usage: call with parsed YAML to determine if it defines a workflow or action.
    >>> workflow_or_action({})
    'action'
    >>> workflow_or_action({'on': {'workflow_call': {}}})
    'workflow'
    """
    on_section = _get_on_section(workflow_def)
    if isinstance(on_section, dict) and "workflow_call" in on_section:
        return "workflow"
    return "action"

def input_placeholder(name, info):
    """Usage: call with an input name and its metadata dict to build an example value."""
    default = info.get("default")
    if default is not None:
        return json.dumps(default)
    return f"<{name}>"

def secret_placeholder(name):
    """Usage: call with a secret key name to produce a `${{ secrets.X }}` placeholder."""
    return f"${{{{ secrets.{name.upper()} }}}}"

def render_workflow_example(workflow_ref, permissions, inputs, secrets, use_optional=False):
    """Usage: call with workflow reference/metadata to render YAML usage snippets."""
    selected_inputs = inputs if use_optional else {
        k: v for k, v in inputs.items() if v.get("required")
    }
    selected_secrets = secrets if use_optional else {
        k: v for k, v in secrets.items() if v.get("required")
    }

    lines = [
        "jobs:",
        "  call-workflow:",
        f"    uses: {workflow_ref}",
    ]

    perm_block = render_permissions_block(permissions, indent="    ")
    if perm_block:
        lines.extend(perm_block)

    if selected_inputs:
        lines.append("    with:")
        for key, val in selected_inputs.items():
            lines.append(f"      {key}: {input_placeholder(key, val)}")

    if selected_secrets:
        lines.append("    secrets:")
        for key in selected_secrets:
            lines.append(f"      {key}: {secret_placeholder(key)}")

    return "\n".join(lines)

def render_action_example(action_ref, permissions, inputs, use_optional=False):
    """Usage: call with action reference/inputs to render sample workflow steps."""
    selected_inputs = inputs if use_optional else {
        k: v for k, v in inputs.items() if v.get("required")
    }

    lines = [
        "jobs:",
        "  call-action:",
        "    runs-on: <runs-on>",
    ]

    perm_block = render_permissions_block(permissions, indent="    ")
    if perm_block:
        lines.extend(perm_block)

    lines.extend([
        "    steps:",
        "      - name: Use action",
        f"        uses: {action_ref}",
    ])

    if selected_inputs:
        lines.append("        with:")
        for key, val in selected_inputs.items():
            lines.append(f"          {key}: {input_placeholder(key, val)}")

    return "\n".join(lines)

def doc_examples(kind, ref, permissions, inputs, secrets):
    """Usage: call with workflow/action metadata to assemble example Markdown blocks."""
    sections = []

    if kind == "workflow":
        full = render_workflow_example(ref, permissions, inputs, secrets, use_optional=True)
        minimal = render_workflow_example(ref, permissions, inputs, secrets, use_optional=False)
    else:
        full = render_action_example(ref, permissions, inputs, use_optional=True)
        minimal = render_action_example(ref, permissions, inputs, use_optional=False)

    sections.append("### Example usage")
    sections.append("#### Full example")
    sections.append(f"```yaml\n{full}\n```")
    sections.append("#### Minimal example")
    sections.append(f"```yaml\n{minimal}\n```")

    return "\n\n".join(sections)

def create_documentation(workflow_def, workflow_ref, action_ref=None):
    """Usage: call with a parsed workflow/action to get the full Markdown doc."""
    kind = workflow_or_action(workflow_def)
    doc_parts = []
    description = workflow_def.get("description")
    _, metadata = extract_autodoc_metadata(description)
    metadata_permissions = metadata.get("permissions") if metadata else None

    if kind == "workflow":
        spec = _get_on_section(workflow_def).get("workflow_call", {})
        inputs = spec.get("inputs", {})
        secrets = spec.get("secrets", {})
        outputs = spec.get("outputs", {})
        permissions = (
            spec.get("permissions")
            or metadata_permissions
            or workflow_def.get("permissions")
            or collect_job_permissions(workflow_def.get("jobs"))
        )

        doc_parts.append("### Inputs")
        if inputs:
            doc_parts.append("\n".join(
                [document_workflow_arg(name=k, **v) for k, v in inputs.items()]
            ))
        else:
            doc_parts.append("There are no inputs for this workflow.")

        if secrets:
            doc_parts.append("\n### Secrets")
            doc_parts.append("\n".join(
                [document_workflow_arg(name=k, **v) for k, v in secrets.items()]
            ))

        if outputs:
            doc_parts.append("\n### Outputs")
            doc_parts.append("\n".join(
                [document_workflow_arg(name=k, **v) for k, v in outputs.items()]
            ))

        permissions_doc = format_permissions(permissions)
        if permissions_doc:
            doc_parts.append("\n### Required permissions")
            doc_parts.append(permissions_doc)

        doc_parts.append("\n" + doc_examples(kind, workflow_ref, permissions, inputs, secrets))
    else:
        inputs = workflow_def.get("inputs", {})
        outputs = workflow_def.get("outputs", {})
        permissions = metadata_permissions or workflow_def.get("permissions")

        doc_parts.append("### Inputs")
        if inputs:
            doc_parts.append("\n".join(
                [document_workflow_arg(name=k, **v) for k, v in inputs.items()]
            ))
        else:
            doc_parts.append("There are no inputs for this action.")

        if outputs:
            doc_parts.append("\n### Outputs")
            doc_parts.append("\n".join(
                [document_workflow_arg(name=k, **v) for k, v in outputs.items()]
            ))

        permissions_doc = format_permissions(permissions)
        if permissions_doc:
            doc_parts.append("\n### Required permissions")
            doc_parts.append(permissions_doc)

        ref = action_ref or workflow_ref
        doc_parts.append("\n" + doc_examples(kind, ref, permissions, inputs, {}))

    return "\n\n".join(doc_parts)

def replace_docstring(src, docstring, start_token="<!-- autodoc start -->", end_token="<!-- autodoc end -->"):
    """
    Usage: call with the target file contents to replace the marked autodoc block.
    >>> src = '''one
    ... two
    ... <!-- autodoc start -->
    ... three
    ... <!-- autodoc end -->
    ... four
    ... five'''
    >>> res = replace_docstring(src, "this\\nwas\\nreplaced")
    >>> print(res)
    one
    two
    <!-- autodoc start -->
    this
    was
    replaced
    <!-- autodoc end -->
    four
    five
    """
    start = re.escape(start_token)
    end = re.escape(end_token)
    pattern = re.compile(rf"({start}).*?({end})", flags=re.IGNORECASE | re.DOTALL)
    return pattern.sub(r"\1\n" + docstring + r"\n\2", src, count=1)


def extract_autodoc_metadata(description):
    """Usage: call with a description string to split out trailing `autodoc` metadata.
    >>> extract_autodoc_metadata("desc\n\n  autodoc:\n    permissions:\n      contents: write")
    ('desc', {'permissions': {'contents': 'write'}})
    >>> extract_autodoc_metadata("just text")
    ('just text', {})
    """
    if not description or not isinstance(description, str):
        return description, {}

    match = re.search(r"(^|\n)(?P<indent>[ \t]*)autodoc:\s*\n(?P<body>[\s\S]+)$", description)
    if not match:
        return description, {}

    start = match.start("indent")
    metadata_block = description[start:]
    cleaned = description[:start].rstrip()

    try:
        parsed = yaml.safe_load(textwrap.dedent(metadata_block)) or {}
    except yaml.YAMLError:
        parsed = {}

    if isinstance(parsed, dict) and "autodoc" in parsed:
        parsed = parsed["autodoc"]

    if not isinstance(parsed, dict):
        parsed = {}

    return cleaned, parsed


def format_permissions(permissions):
    """Usage: call with permissions payload to get Markdown bullet output."""
    if not permissions:
        return ""

    if isinstance(permissions, str):
        return f"- `{permissions}`"

    if isinstance(permissions, (list, tuple, set)):
        return "\n".join(f"- `{item}`" for item in permissions)

    if isinstance(permissions, dict):
        return "\n".join(
            f"- `{scope}`: `{level}`" for scope, level in permissions.items()
        )

    return ""


def render_permissions_block(permissions, indent=""):
    """Usage: call with permissions payload to embed YAML snippets in examples."""
    if not permissions:
        return []

    if isinstance(permissions, dict):
        lines = [f"{indent}permissions:"]
        for scope, level in permissions.items():
            lines.append(f"{indent}  {scope}: {level}")
        return lines

    if isinstance(permissions, str):
        return [f"{indent}permissions: {permissions}"]

    if isinstance(permissions, (list, tuple, set)):
        lines = [f"{indent}permissions:"]
        for scope in permissions:
            lines.append(f"{indent}  {scope}: write")
        return lines

    return []


def collect_job_permissions(jobs_section):
    """Usage: call with the `jobs` mapping to merge job-specific permissions."""
    if not isinstance(jobs_section, dict):
        return None

    aggregated = {}
    found = False
    for job in jobs_section.values():
        if not isinstance(job, dict):
            continue
        job_permissions = job.get("permissions")
        if isinstance(job_permissions, dict):
            aggregated.update(job_permissions)
            found = True
    return aggregated if found else None

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
        "--commit-message",
        dest="commit_message",
        default="docs: update autogenerated docs",
        required=False,
        help="Commit message to use after updating the documentation",
    )
    parser.add_argument(
        "--author",
        dest="author",
        default="github-actions[bot]",
        required=False,
        help="Author name to use for git commits",
    )
    parser.add_argument(
        "--author-email",
        dest="author_email",
        default="github-actions[bot]@users.noreply.github.com",
        required=False,
        help="Author email to use for git commits",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        required=False,
        help="Enable verbose logging and preview the diff without writing files",
    )
    parser.add_argument(
        "--skip-commit",
        dest="skip_commit",
        action="store_true",
        required=False,
        help="Update the doc file but skip git add/commit/push",
    )
    args = parser.parse_args()

    if not args.workflow_file:
        parser.error("--workflow-file (or INPUT_WORKFLOW_FILE) is required")
    if not args.doc_file:
        parser.error("--doc-file (or INPUT_DOC_FILE) is required")

    workflow_path = os.path.abspath(args.workflow_file)
    doc_path = os.path.abspath(args.doc_file)
    debug_log(args.debug, f"Loading workflow definition from {workflow_path}")
    with open(workflow_path, "r", encoding="utf-8") as wf:
        workflow = yaml.load(wf, Loader=yaml.CLoader)
    with open(doc_path, "r", encoding="utf-8") as doc_file:
        original_readme = doc_file.read()

    repo_info = detect_repo_info(workflow_path, args.debug)
    workflow_ref = repo_info["workflow_ref"]
    action_ref = repo_info["action_ref"]
    debug_log(args.debug, f"Generating documentation for ref '{workflow_ref}'.")

    docstring = create_documentation(workflow, workflow_ref, action_ref)
    updated_readme = replace_docstring(original_readme, docstring, args.start_token, args.end_token)

    if updated_readme == original_readme:
        debug_log(args.debug, "No changes detected; skipping file update and commit.")
        sys.exit(0)

    if args.debug:
        diff = difflib.unified_diff(
            original_readme.splitlines(),
            updated_readme.splitlines(),
            fromfile=f"{doc_path} (original)",
            tofile=f"{doc_path} (updated)",
            lineterm="",
        )
        diff_text = "\n".join(diff)
        if diff_text:
            print("[autodoc] Debug diff preview:\n" + diff_text)
        else:
            print("[autodoc] Debug mode enabled but no diff produced.")
        debug_log(args.debug, "Debug mode - not writing file or committing changes.")
        sys.exit(0)

    with open(doc_path, "w", encoding="utf-8") as doc_file:
        doc_file.write(updated_readme)
    debug_log(args.debug, f"Wrote updated documentation to {doc_path}.")

    if args.skip_commit:
        debug_log(args.debug, "--skip-commit enabled; exiting before git operations.")
        sys.exit(0)

    repo_root = repo_info["repo_root"]
    if not repo_root:
        print("Error: Unable to determine git repository root; cannot commit changes.", file=sys.stderr)
        sys.exit(1)

    doc_rel = os.path.relpath(doc_path, repo_root)
    commit_env = os.environ.copy()
    commit_env.update(
        {
            "GIT_AUTHOR_NAME": args.author,
            "GIT_AUTHOR_EMAIL": args.author_email,
            "GIT_COMMITTER_NAME": args.author,
            "GIT_COMMITTER_EMAIL": args.author_email,
        }
    )

    try:
        debug_log(args.debug, f"Staging {doc_rel} for commit.")
        subprocess.check_call(["git", "add", doc_rel], cwd=repo_root)
        subprocess.check_call(["git", "commit", "-m", args.commit_message], cwd=repo_root, env=commit_env)
        debug_log(args.debug, f"Committed changes to {doc_rel} with message '{args.commit_message}'.")
    except subprocess.CalledProcessError as exc:
        print(f"Error committing documentation changes: {exc}", file=sys.stderr)
        sys.exit(exc.returncode)

    branch = repo_info["branch"]

    try:
        debug_log(args.debug, f"Pushing branch {branch} to origin.")
        subprocess.check_call(["git", "push", "origin", branch], cwd=repo_root)
        debug_log(args.debug, f"Pushed changes on branch {branch}.")
    except subprocess.CalledProcessError as exc:
        print(f"Error pushing documentation changes: {exc}", file=sys.stderr)
        sys.exit(exc.returncode)
