#!/usr/bin/env node
/**
 * Build one render-blocking CSS file from Pico + the site styles.
 * The shield still fetches css/main.css separately when it maps class names.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const cssDir = path.join(root, 'css');

const pico = fs.readFileSync(path.join(cssDir, 'pico.min.css'), 'utf8')
  .replace(/^@charset\s+["'][^"']+["'];\s*/i, '');
const main = fs.readFileSync(path.join(cssDir, 'main.css'), 'utf8');

const output = `@charset "UTF-8";\n${pico}\n${main}`;
fs.writeFileSync(path.join(cssDir, 'site.min.css'), output);
console.log(`Built css/site.min.css (${(output.length / 1024).toFixed(1)} KiB)`);
