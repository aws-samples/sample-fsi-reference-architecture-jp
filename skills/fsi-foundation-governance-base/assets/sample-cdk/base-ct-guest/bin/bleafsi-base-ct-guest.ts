/* ⚠️ SECURITY NOTICE — REFERENCE SAMPLE.
 * This governance-base guest sample is a reference starting point, not a drop-in production stack.
 * The bundled IAM sample roles are intentionally broad and must be narrowed to least privilege.
 * See assets/sample-cdk/base-ct-guest/SECURITY_NOTICE.md before real use. */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BaseCTStack } from '../lib/bleafsi-base-ct-guest-stack';
import { PjPrefix, DevParameter, StageParameter, ProdParameter } from './parameter';

/*
 * Control Tower ゲストアカウントの東京リージョンにガバナンスベースをデプロイ
 */

const app = new cdk.App();
// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This governance-base guest sample is a reference starting point. The bundled IAM ' +
    'sample roles are intentionally broad (SysAdmin NotAction iam:*, InstanceOps ec2:*) and meant ' +
    'to be narrowed to least privilege; S3 data-event logging is off by default; the default-SG ' +
    'auto-remediation runs automatically. Review IAM scope, enable S3 data events where needed, and ' +
    'confirm the security notification email before real use. See assets/sample-cdk/base-ct-guest/SECURITY_NOTICE.md.',
);
const envTagName = 'Environment';

// スタック作成
// for Development
const DevPrimaryStack = new BaseCTStack(app, `${PjPrefix}-Primary-Dev`, {
  description: 'BLEA for FSI Governance base (uksb-1tupboc63) (tag:bleafsi-base-ct-guest)',
  ...DevParameter,
  env: {
    account: DevParameter.account,
    region: DevParameter.primary.region,
  },
});
// Tagging "Environment" tag to all resources in this app
cdk.Tags.of(DevPrimaryStack).add(envTagName, DevParameter.envName);

//Secondary regionが定義されている場合のみ
if (DevParameter.secondary != null) {
  const DevSecondaryStack = new BaseCTStack(app, `${PjPrefix}-Secondary-Dev`, {
    ...DevParameter,
    env: {
      account: DevParameter.account,
      region: DevParameter.secondary.region,
    },
  });
  // Tagging "Environment" tag to all resources in this app
  cdk.Tags.of(DevSecondaryStack).add(envTagName, DevParameter.envName);
}

// for Staging
// const StageStack = new BaseCTStack(app, `${PjPrefix}-Stage`, StageParameter);

// for Production
// const ProdStack = new BaseCTStack(app, `${PjPrefix}-Prod`, ProdParameter);

// for CT AFC use
new BaseCTStack(app, `${PjPrefix}-AFC`, {
  ...DevParameter,
});

// Tagging "Environment" tag to all resources in this app
//cdk.Tags.of(StageStack).add(envTagName, StageParameter.envName);
//cdk.Tags.of(ProdStack).add(envTagName, ProdParameter.envName);
