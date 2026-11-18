const assert = require("node:assert/strict");
const test = require("node:test");
const config = require("../release.config.js");

test("the release configuration renders a fix and its body with the locked preset", async () => {
  const pluginName = "@semantic-release/release-notes-generator";
  const [, options] = config.plugins.find(
    (plugin) => Array.isArray(plugin) && plugin[0] === pluginName,
  );
  const { generateNotes } = await import(pluginName);

  // Run only the notes hook; no Git remotes, credentials, or publishing plugins.
  const notes = await generateNotes(options, {
    cwd: process.cwd(),
    options: { repositoryUrl: "https://github.com/example/example.git" },
    commits: [
      {
        hash: "0123456789abcdef0123456789abcdef01234567",
        message: "fix: preserve release notes\n\nKeep this explanation in the notes.",
      },
    ],
    lastRelease: { gitTag: "v2.2.0" },
    nextRelease: { gitTag: "v2.2.1", version: "2.2.1" },
  });

  assert.match(notes, /## .*2\.2\.1/);
  assert.match(notes, /compare\/v2\.2\.0\.\.\.v2\.2\.1/);
  assert.match(notes, /^\* fix: preserve release notes$/m);
  assert.match(notes, /^  _Keep this explanation in the notes\._$/m);
});
