module.exports = {
    uiPort: process.env.PORT || 1880,
    flowFile: "flows.json",
    flowFilePretty: true,
    credentialSecret: false,
    ui: { path: "ui" },
    logging: { console: { level: "info", metrics: false, audit: false } },
};
