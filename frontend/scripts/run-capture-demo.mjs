import { spawnSync } from 'node:child_process';

process.env.CAPTURE_DEMO = '1';
const result = spawnSync(
  'npx',
  ['playwright', 'test', 'tests/capture-demo.spec.ts', '--project=chromium'],
  { stdio: 'inherit', env: process.env, shell: true },
);
process.exit(result.status ?? 1);
