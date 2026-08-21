/* ⚠️ SECURITY NOTICE — REFERENCE SAMPLE.
 * This governance-base logging sample is a reference starting point, not a drop-in production stack.
 * The aggregated log bucket policy does not enable Object Lock / MFA Delete on its own.
 * See assets/sample-cdk/base-ct-logging/SECURITY_NOTICE.md before real use. */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BaseCTStack } from '../lib/bleafsi-base-ct-logging-stack';
import { PjPrefix, DevParameter, StageParameter, ProdParameter } from './parameter';

/*
 * Control Tower Log Archiveアカウントにログ集約 S3 バケットを作成
 */

const app = new cdk.App();
// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This governance-base logging sample is a reference starting point. The aggregated ' +
    'log bucket policy denies object and version deletion but does not enable Object Lock / MFA ' +
    'Delete on its own, so strong log immutability requires additional hardening downstream. ' +
    'See assets/sample-cdk/base-ct-logging/SECURITY_NOTICE.md.',
);

// スタック作成
// for Development
const DevStack = new BaseCTStack(app, `${PjPrefix}-Dev`, {
  env: DevParameter.env,
});

// for Staging
/*const StageStack = new BaseCTStack(app, `${PjPrefix}-Stage`, {
  env: StageParameter.env,
});*/

// for Production
/*const ProdStack = new BaseCTStack(app, `${PjPrefix}-Prod`, {
  env: ProdParameter.env,
});*/

// Tagging "Environment" tag to all resources in this app
const envTagName = 'Environment';
cdk.Tags.of(DevStack).add(envTagName, DevParameter.envName);
//cdk.Tags.of(StageStack).add(envTagName, StageParameter.envName);
//cdk.Tags.of(ProdStack).add(envTagName, ProdParameter.envName);
