#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const stickyStartRe = /^[的地得了着过里中内外吗呢吧啊呀啦嘛么]/u;
const badAsrTextRe = /录出|音樂|汽水音樂|收藏家|一手|歌慌|接著|裡/u;

const compact = (text) => String(text ?? "").replace(/\s+/g, "");
const stripLeadingMarks = (text) => String(text ?? "").replace(/^[\s\p{P}]+/u, "");

const collectSegmentFiles = (inputPath) => {
  const resolved = path.resolve(inputPath);
  if (!fs.existsSync(resolved)) throw new Error(`Path does not exist: ${resolved}`);

  const stat = fs.statSync(resolved);
  if (stat.isFile()) return resolved.endsWith(".segments.json") ? [resolved] : [];

  const files = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const child = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(child);
      else if (entry.isFile() && entry.name.endsWith(".segments.json")) files.push(child);
    }
  };
  walk(resolved);
  return files.sort();
};

const validateFile = (file) => {
  const json = JSON.parse(fs.readFileSync(file, "utf8"));
  const errors = [];

  if (json.source !== "script-text+asr-timing") {
    errors.push(`source is ${JSON.stringify(json.source)}, expected "script-text+asr-timing"`);
  }

  if (!json.scriptText) errors.push("missing scriptText");
  if (!Array.isArray(json.segments) || !json.segments.length) errors.push("missing segments");

  const segmentText = compact((json.segments || []).map((segment) => segment.text).join(""));
  const scriptText = compact(json.scriptText);
  if (json.scriptText && segmentText !== scriptText) {
    errors.push("joined segment text does not match scriptText after whitespace normalization");
  }

  for (const term of json.protectedTerms || []) {
    const normalizedTerm = compact(term);
    if (!normalizedTerm || !scriptText.includes(normalizedTerm)) continue;
    const inOneSegment = json.segments.some((segment) => compact(segment.text).includes(normalizedTerm));
    if (!inOneSegment) errors.push(`protected term split across cues: ${term}`);
  }

  const stickyStarts = (json.segments || [])
    .map((segment) => stripLeadingMarks(segment.text))
    .filter((text) => stickyStartRe.test(text));
  if (stickyStarts.length) errors.push(`cue starts with left-bound suffix: ${stickyStarts.join(" | ")}`);

  const badMatch = badAsrTextRe.exec(JSON.stringify(json.segments || []));
  if (badMatch) errors.push(`possible ASR homophone text found: ${badMatch[0]}`);

  return { file, errors };
};

const inputs = process.argv.slice(2);
if (!inputs.length) {
  console.error("Usage: validate_segments.mjs <segments.json | directory> [...]");
  process.exit(2);
}

let files = [];
for (const input of inputs) files = files.concat(collectSegmentFiles(input));
files = [...new Set(files)];

if (!files.length) {
  console.error("No .segments.json files found.");
  process.exit(2);
}

let failed = false;
for (const result of files.map(validateFile)) {
  if (result.errors.length) {
    failed = true;
    console.error(`FAIL ${result.file}`);
    for (const error of result.errors) console.error(`  - ${error}`);
  } else {
    console.log(`PASS ${result.file}`);
  }
}

process.exit(failed ? 1 : 0);
