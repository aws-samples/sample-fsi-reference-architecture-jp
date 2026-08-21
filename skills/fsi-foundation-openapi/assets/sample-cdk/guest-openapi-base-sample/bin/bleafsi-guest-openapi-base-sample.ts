/* ⚠️ SECURITY NOTICE — REFERENCE / DEMO SAMPLE, NOT PRODUCTION-READY.
 * WAF managed rules run count-only (non-blocking) with no rate limit and Cognito
 * allows password auth with MFA optional. Harden before any real use.
 * See assets/sample-cdk/guest-openapi-base-sample/SECURITY_NOTICE.md. */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SampleOpenApiStack } from '../lib/bleafsi-openapi-base-sample-stack';
import { PjPrefix, DevParameter, StageParameter, ProdParameter } from './parameter';

const app = new cdk.App();

// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This is a reference/demo sample, NOT production-ready. WAF managed rules run in ' +
    'count-only (non-blocking) mode with no rate limit, and Cognito allows USER_PASSWORD_AUTH / ' +
    'adminUserPassword with MFA optional. Switch WAF to block + add rate limiting and move to ' +
    'SRP + required MFA before any real use. See assets/sample-cdk/guest-openapi-base-sample/SECURITY_NOTICE.md.',
);

// スタック作成
// for Development
const DevStack = new SampleOpenApiStack(app, `${PjPrefix}-Dev`, {
  description: 'BLEA for FSI OpenAPI base (uksb-1tupboc63) (tag:guest-openapi-base-sample)',
  ...DevParameter,
});

//for Staging
//const StageStack = new SampleOpenApiStack(app, `${PjPrefix}-Stage`, StageParameter);

//for Production
//const ProdStack = new SampleOpenApiStack(app, `${PjPrefix}-Prod`, ProdParameter);

// --------------------------------- Tagging  -------------------------------------

// Tagging "Environment" tag to all resources in this app
const envTagName = 'Environment';
cdk.Tags.of(DevStack).add(envTagName, DevParameter.envName);
// cdk.Tags.of(StageStack).add(envTagName, StageParameter.envName);
// cdk.Tags.of(ProdStack).add(envTagName, ProdParameter.envName);
