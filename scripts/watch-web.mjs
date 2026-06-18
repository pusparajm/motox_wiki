#!/usr/bin/env node
/**
 * Rebuild obfuscated js/dist whenever public JS sources change.
 */
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const sources = [
  path.join(root, 'js', 'shield.js'),
  path.join(root, 'js', 'core.js'),
  path.join(root, 'js', 'search.js')
];

let building = false;
let pending = false;
let debounceTimer = null;

function runBuild() {
  if (building) {
    pending = true;
    return;
  }
  building = true;
  pending = false;

  const child = spawn('npm', ['run', 'build:web'], {
    cwd: root,
    stdio: 'inherit',
    shell: process.platform === 'win32'
  });

  child.on('exit', code => {
    building = false;
    if (code === 0) {
      console.log('[watch:web] rebuild complete');
    } else {
      console.error(`[watch:web] rebuild failed (exit ${code})`);
    }
    if (pending) runBuild();
  });
}

function scheduleBuild(label) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    console.log(`[watch:web] ${label} — rebuilding…`);
    runBuild();
  }, 200);
}

console.log('[watch:web] watching public JS sources…');
runBuild();

for (const file of sources) {
  fs.watch(file, { persistent: true }, () => scheduleBuild(path.basename(file)));
}

process.stdin.resume();
