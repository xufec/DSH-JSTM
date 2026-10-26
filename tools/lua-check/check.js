#!/usr/bin/env node
/* Lua 5.1 syntax check for the files this project injects into the game.
 *
 * The embedded local server is injected as *source* into the game's plain-text
 * assets/src/config.luac, so a syntax slip breaks the whole client start-up.
 * luaparse is a real Lua parser, so this catches what a naive bracket counter
 * cannot (brackets inside strings/comments used to false-positive, which once
 * silently dropped the whole embedded server from the build).
 *
 * usage:
 *   node tools/lua-check/check.js <file.lua> [...]        # report
 *   node tools/lua-check/check.js --quiet <file.lua>      # exit code only
 */
const fs = require('fs');
const path = require('path');

// minimal fallback parser for stripping a leading Lua comment block
const luaparse = require(path.join(__dirname, 'node_modules', 'luaparse'));

const argv = process.argv.slice(2);
const quiet = argv.includes('--quiet');
const files = argv.filter((a) => a !== '--quiet');

if (!files.length) {
  if (!quiet) console.error('usage: node check.js [--quiet] <file.lua> [...]');
  process.exit(2);
}

let bad = 0;
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  try {
    luaparse.parse(src, { luaVersion: '5.1' });
    if (!quiet) console.log('OK    ' + f + '  (' + src.length + ' bytes)');
  } catch (e) {
    bad++;
    if (quiet) {
      console.error(path.basename(f) + ': ' + e.message);
    } else {
      console.log('FAIL  ' + f);
      console.log('      ' + e.message);
    }
  }
}
process.exit(bad ? 1 : 0);
