// Keep the older entry point, using the current continuous indoor acceptance route.
// Unlike the retired terrace approach, this walks both stacked stairs up and down,
// operates doors through the visitor's F interaction, and never teleports mid-route.
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root = resolve(import.meta.dirname, '..');
process.env.T5_CHECK_OUT ||= 'evidence/tirumala-5-stacked-stair';
await import('./check_tirumala_5_revision.mjs');
const report = JSON.parse(readFileSync(resolve(root, process.env.T5_CHECK_OUT, 'runtime-acceptance.json'), 'utf8'));
const out = resolve(root, 'output/tirumala-5-delivery');
mkdirSync(out, {recursive: true});
writeFileSync(resolve(out, 'complete-stair-route.json'), JSON.stringify({
  planHash: report.planHash,
  segments: report.routes,
  passed: report.passed,
  initialSpawns: report.initialSpawns,
  laterTeleports: report.laterTeleports,
  checks: report.checks,
  failure: report.failure,
}, null, 2) + '\n');
