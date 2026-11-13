# Built from this file at the action ref (see action.yaml), so the image always
# matches the ref a consumer pins. The script only uses the standard library,
# so no packages are installed: nothing to pin, and no extra CVE surface.
FROM python:3.14-alpine@sha256:5862d971d1f0ae26b258cefa4e893556b1d3aba81bd2ff30888704ad378bab67

COPY autodoc.py /autodoc.py

WORKDIR /github/workspace/

# -I (isolated mode): ignore PYTHON* variables and never put the working
# directory, which holds the PR's files, on sys.path.
ENTRYPOINT ["python3", "-I", "/autodoc.py"]
