import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PjPrefix, DevParameter, StageParameter, ProdParameter } from './parameter';
import { GuestMarketDataStack } from '../lib/bleafsi-guest-market-data-stack';

/*
 * BLEA-FSI Market Data Sample application stack
 *
 * ⚠️ SECURITY NOTICE — REFERENCE / DEMO SAMPLE, NOT PRODUCTION-READY.
 * Authentication, TLS, per-subscriber entitlement, and least-privilege roles are
 * deliberately left to the implementer. False or stale market prices can drive
 * erroneous trades. See assets/sample-cdk/SECURITY_NOTICE.md before any real use.
 */

const app = new cdk.App();

// Emit the security notice on every `cdk synth` / `cdk deploy` (prints to stderr).
console.error(
  'SECURITY: This is a reference/demo sample, NOT production-ready. The Distributor ALB is ' +
    'plain HTTP with open:true and no authentication Lambda is wired, there is no per-subscriber ' +
    'entitlement, all tiers share one wildcarded Kinesis task role (stream/*), and the container ' +
    'base image is unpinned. False or stale market prices can drive erroneous trades. Add ' +
    'authentication, TLS, entitlement, least-privilege roles, and image pinning before any real ' +
    'use. See assets/sample-cdk/SECURITY_NOTICE.md for the full list.',
);

// ----------------------- Guest Market Data System Stacks for development ------------------------------
const devStack = new GuestMarketDataStack(app, `${PjPrefix}-Dev`, {
  description: 'BLEA for FSI Market Data (uksb-1tupboc63) (tag:guest-market-data-sample)',
  ...DevParameter,
});

// // ----------------------- Guest Market Data System Stacks for staging ------------------------------
// const stagingStack = new GuestMarketDataStack(app, `${PjPrefix}-Stage`, DevParameter);

// // ----------------------- Guest Market Data System Stacks for production ------------------------------
// const prodStack = new GuestMarketDataStack(app, `${PjPrefix}-Prod`, DevParameter);

// --------------------------------- Tagging  -------------------------------------
// Tagging "Environment" tag to all resources in this app
const envTagName = 'Environment';
cdk.Tags.of(devStack).add(envTagName, DevParameter.envName);
// cdk.Tags.of(stagingStack).add(envTagName, StageParameter.envName);
// cdk.Tags.of(prodStack).add(envTagName, ProdParameter.envName);
