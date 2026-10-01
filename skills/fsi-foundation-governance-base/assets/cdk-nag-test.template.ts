/**
 * cdk-nag enforcement test template (BLEA for FSI pattern).
 *
 * Purpose: enforce cdk-nag on the CDK you write from this skill. It mirrors the pattern used by
 * the BLEA-FSI reference implementation (usecases/<usecase>/test/*.test.ts):
 *   1. apply AwsSolutionsChecks to every stack via Aspects,
 *   2. fail the test on any UNSUPPRESSED AwsSolutions-* finding (the CI gate),
 *   3. suppress exceptions only with a written `reason` (audit discipline).
 *
 * How to use:
 *   1. Copy this file into your CDK project's test/ directory (rename to <your-stack>.test.ts).
 *   2. Replace the placeholder import and stack instantiation with your own stack(s).
 *   3. For each finding you have judged acceptable, add a NagSuppressions entry WITH a reason.
 *      See references/cdk-nag.md for the suppression ledger (which rules the reference
 *      implementation suppressed for this workload, and why) — do NOT blanket-copy them; only
 *      suppress findings you have actually reviewed for your own stack.
 *   4. Run your test runner (e.g. `npm test`). An unsuppressed AwsSolutions-* finding fails CI.
 *
 * Requires: aws-cdk-lib, cdk-nag, and a test runner (jest assumed below).
 */
import * as cdk from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';

// TODO: import your own stack(s).
// import { MyWorkloadStack } from '../lib/my-workload-stack';

const app = new cdk.App();

// TODO: instantiate the stack(s) you want checked. Provide the env/props your stack requires.
// const stack = new MyWorkloadStack(app, 'MyWorkloadStack', {
//   env: { account: process.env.CDK_DEFAULT_ACCOUNT ?? '111111111111', region: 'ap-northeast-1' },
// });
declare const stack: cdk.Stack; // placeholder — remove once the line above is uncommented.

describe('cdk-nag AwsSolutions Pack', () => {
  beforeAll(() => {
    // 3) Suppress ONLY reviewed exceptions, each with an explicit reason (kept as audit evidence).
    // Example (delete and replace with your own reviewed suppressions):
    // NagSuppressions.addResourceSuppressionsByPath(
    //   stack,
    //   '/MyWorkloadStack/SomeRole/DefaultPolicy/Resource',
    //   [{ id: 'AwsSolutions-IAM5', reason: 'Scoped to deploy-time actions only.' }],
    // );

    // 1) Apply the AwsSolutions pack to the stack. Do this for EVERY stack you create.
    cdk.Aspects.of(stack).add(new AwsSolutionsChecks());
  });

  // 2) The gate: any unsuppressed AwsSolutions-* finding fails this test (and thus CI).
  test('No unsuppressed AwsSolutions errors', () => {
    const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
    try {
      expect(errors).toHaveLength(0);
    } catch (e) {
      // Surface the actual findings to make CI failures actionable.
      const messages = errors.map((err) => ({ id: err.id, type: err.entry.type, data: err.entry.data }));
      // eslint-disable-next-line no-console
      console.error(JSON.stringify(messages, undefined, 2));
      throw e;
    }
  });
});
