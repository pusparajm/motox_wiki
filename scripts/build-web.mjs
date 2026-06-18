#!/usr/bin/env node
/**
 * Obfuscate public wiki JavaScript for production deploy.
 * Usage: npm run build:web
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import JavaScriptObfuscator from 'javascript-obfuscator';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const jsDir = path.join(root, 'js');
const distDir = path.join(jsDir, 'dist');

const FILES = ['shield.js', 'core.js', 'search.js'];

const OBF_OPTIONS = {
  compact: true,
  controlFlowFlattening: true,
  controlFlowFlatteningThreshold: 0.4,
  deadCodeInjection: true,
  deadCodeInjectionThreshold: 0.15,
  identifierNamesGenerator: 'hexadecimal',
  renameGlobals: false,
  selfDefending: true,
  stringArray: true,
  stringArrayEncoding: ['rc4'],
  stringArrayThreshold: 0.8,
  transformObjectKeys: true,
  unicodeEscapeSequence: false,
  target: 'browser'
};

if (!fs.existsSync(distDir)) fs.mkdirSync(distDir, { recursive: true });

for (const file of FILES) {
  const src = path.join(jsDir, file);
  const code = fs.readFileSync(src, 'utf8');
  const result = JavaScriptObfuscator.obfuscate(code, OBF_OPTIONS);
  fs.writeFileSync(path.join(distDir, file), result.getObfuscatedCode());
  console.log(`Obfuscated ${file} → js/dist/${file}`);
}

console.log('Done. Point HTML script tags to js/dist/ for production, or copy dist/* over js/ before deploy.');
