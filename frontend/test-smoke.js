/**
 * Frontend smoke test for Seva AI admin panel & main client.
 * Verifies production artifacts, asset chunking, and lazy loading.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distDir = path.join(__dirname, "dist");
const assetsDir = path.join(distDir, "assets");

console.log("Running frontend smoke tests...");

// 1. Verify dist/index.html exists
if (!fs.existsSync(path.join(distDir, "index.html"))) {
  console.error("FAIL: dist/index.html not found! Run npm run build first.");
  process.exit(1);
}
console.log("PASS: dist/index.html exists.");

// 2. Verify assets directory exists
if (!fs.existsSync(assetsDir)) {
  console.error("FAIL: dist/assets directory not found!");
  process.exit(1);
}

const assetFiles = fs.readdirSync(assetsDir);

// 3. Verify separate lazy-loaded AdminPanel chunk was generated
const adminJsChunk = assetFiles.find((f) => f.startsWith("AdminPanel-") && f.endsWith(".js"));
if (!adminJsChunk) {
  console.error("FAIL: Lazy-loaded AdminPanel JS bundle chunk was not generated!");
  process.exit(1);
}
console.log(`PASS: Found lazy-loaded admin bundle: ${adminJsChunk}`);

// 4. Verify main client bundle exists
const mainJsChunk = assetFiles.find((f) => f.startsWith("index-") && f.endsWith(".js"));
if (!mainJsChunk) {
  console.error("FAIL: Main client index JS bundle not found!");
  process.exit(1);
}
console.log(`PASS: Found main client bundle: ${mainJsChunk}`);

// 5. Verify admin theme CSS is bundled
const adminCssChunk = assetFiles.find((f) => f.startsWith("AdminPanel-") && f.endsWith(".css"));
if (!adminCssChunk) {
  console.error("FAIL: Admin CSS stylesheet chunk not found!");
  process.exit(1);
}
console.log(`PASS: Found admin theme stylesheet: ${adminCssChunk}`);

console.log("ALL FRONTEND SMOKE TESTS PASSED!");

