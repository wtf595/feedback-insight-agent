import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const webRoot = path.join(projectRoot, "web");

const [html, css, javascript] = await Promise.all([
  readFile(path.join(webRoot, "index.html"), "utf8"),
  readFile(path.join(webRoot, "styles.css"), "utf8"),
  readFile(path.join(webRoot, "app.js"), "utf8"),
]);

if (/<\/style/i.test(css) || /<\/script/i.test(javascript)) {
  throw new Error("Cannot inline assets containing closing style or script tags.");
}

const stylesheetTag = '<link rel="stylesheet" href="./styles.css" />';
const scriptTag = '<script src="./app.js"></script>';

if (!html.includes(stylesheetTag) || !html.includes(scriptTag)) {
  throw new Error("Expected local stylesheet and script tags were not found.");
}

const standalone = html
  .replace(stylesheetTag, () => `<style>\n${css}\n    </style>`)
  .replace(scriptTag, () => `<script>\n${javascript}\n    </script>`);

const outputDirectory = path.join(projectRoot, "dist");
const outputPath = path.join(outputDirectory, "feedback-insight-agent.html");
await mkdir(outputDirectory, { recursive: true });
await writeFile(outputPath, standalone);

console.log(outputPath);
