import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PjPrefix, DevParameters, StageParameters, ProdParameters } from './parameter';
import { SimpleDataLakeStack } from '../lib/bleafsi-guest-simple-datalake-stack';

/*
 * BLEA-FSI Analytics Simple data lake Sample application stack
 *
 * ⚠️ SECURITY NOTICE — REFERENCE / DEMO SAMPLE, NOT PRODUCTION-READY.
 * The Glue ETL scripts "mask" PII (CIF / account numbers) with reverse(), which is
 * trivially reversible and propagates to the BI-readable normalized/analytics layers;
 * the ETL also deletes S3 prefixes unconditionally. Replace reverse() with
 * hashing/tokenization/Lake Formation and add target allow-listing + versioning before
 * any real use. See assets/sample-cdk/SECURITY_NOTICE.md for the full list.
 */

const app = new cdk.App();
// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This is a reference/demo sample, NOT production-ready. PII "masking" in the ' +
    'Glue ETL scripts uses reverse() which is trivially reversible (NOT real masking); the ' +
    'normalized/analytics layers are readable by BI users, so CIF/account numbers can be ' +
    're-identified. ETL also deletes S3 prefixes unconditionally. Replace reverse() with ' +
    'hashing/tokenization/Lake Formation and add target allow-listing + versioning before any ' +
    'real use. See assets/sample-cdk/SECURITY_NOTICE.md for the full list.',
);

// ----------------------- Guest System Stacks for development ------------------------------
//Simple DataLake リソースのプロビジョニング
const devStack = new SimpleDataLakeStack(app, `${PjPrefix}-SimpleDataLake-Dev`, {
  description: 'BLEA for FSI Data Analytics Platform (uksb-1tupboc63) (tag:guest-analytics-platform-sample)',
  ...DevParameters,
});

// // ----------------------- Guest System Stacks for staging ------------------------------
// const stagingStack = new SimpleDataLakeStack(app, `${PjPrefix}-SimpleDataLake-Stage`, StageParameters);

// // ----------------------- Guest System Stacks for production ------------------------------
// const prodStack = new SimpleDataLakeStack(app, `${PjPrefix}-SimpleDataLake-Prod`, ProdParameters);

// --------------------------------- Tagging  -------------------------------------
// Tagging "Environment" tag to all resources in this app
const envTagName = 'Environment';
cdk.Tags.of(devStack).add(envTagName, DevParameters.envName);
//cdk.Tags.of(devStack).add(envTagName, StageParameters.envName);
//cdk.Tags.of(devStack).add(envTagName, ProdParameters.envName);
