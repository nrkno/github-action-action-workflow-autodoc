module.exports = {
  branches: ["main"],
  plugins: [
    "@semantic-release/commit-analyzer",
    [
      "@semantic-release/release-notes-generator",
      {
        // Preset v10 requires changelog writer v9; this plugin uses writer v8.
        preset: "conventionalcommits",
        writerOpts: {
          commitPartial: `* {{header}}
{{#if body}}
  _{{{body}}}_
{{/if}}
`,
        },
      },
    ],
    ["@semantic-release/github"],
  ],
};
