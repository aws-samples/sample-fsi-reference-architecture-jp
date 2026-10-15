/* ⚠️ SECURITY NOTICE — REFERENCE / DEMO SAMPLE, NOT PRODUCTION-READY.
 * The Keycloak-to-Aurora DB link is plaintext (useSSL=false), the DB security group
 * allows the whole VPC CIDR on 3306, and mTLS/FAPI client-auth checks are loose.
 * See assets/sample-cdk/guest-openapi-fapi-sample/SECURITY_NOTICE.md. */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { OpenApiFapiStack } from '../lib/primary/bleafsi-guest-openapi-fapi-stack';
import { PjPrefix, DevParameter, StageParameter, ProdParameter } from './parameter';

const app = new cdk.App();

// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This is a reference/demo FAPI sample, NOT production-ready. The Keycloak-to-Aurora ' +
    'DB link is plaintext (useSSL=false), the DB security group allows the whole VPC CIDR on 3306, ' +
    'and the mTLS/FAPI client-auth checks are loose. Enable DB TLS, tighten the SG, and enforce ' +
    'strict FAPI mTLS before any real use. See assets/sample-cdk/guest-openapi-fapi-sample/SECURITY_NOTICE.md.',
);

// スタック作成
//for Development
const DevPrimaryStack = new OpenApiFapiStack(app, `${PjPrefix}-primary-Dev`, {
  description: 'BLEA for FSI OpenAPI fapi (uksb-1tupboc63) (tag:guest-openapi-fapi-sample)',
  ...DevParameter,
  env: {
    account: DevParameter.account,
    region: DevParameter.primaryRegion.region,
  },
});

//for Staging
/*const StagePrimaryStack = new OpenApiFapiStack(app, `${PjPrefix}-primary-Stage`, {
  ...StageParameter,
  env: {
    account: StageParameter.account,
    region: StageParameter.primaryRegion.region,
  },
}); */

//for Production
/*const ProdPrimaryStack = new OpenApiFapiStack(app, `${PjPrefix}-primary-Prod`, {
  ...ProdParameter,
  env: {
    account: ProdParameter.account,
    region: ProdParameter.primaryRegion.region,
  },
}); */

// --------------------------------- Tagging  -------------------------------------

// Tagging "Environment" tag to all resources in this app
const envTagName = 'Environment';
cdk.Tags.of(DevPrimaryStack).add(envTagName, DevParameter.envName);
// cdk.Tags.of(StagePrimaryStack).add(envTagName, StageParameter.envName);
// cdk.Tags.of(ProdPrimaryStack).add(envTagName, ProdParameter.envName);
