import { Construct } from 'constructs';
import * as synthetics from 'aws-cdk-lib/aws-synthetics';
import { Duration } from 'aws-cdk-lib';
import { join } from 'path';
import { IVpc, SubnetType } from 'aws-cdk-lib/aws-ec2';

export interface CanaryProps {
  vpc: IVpc;
  /**
   * @example https://api.example.com
   */
  targetApiUrl: string;
}

export class Canary extends Construct {
  readonly canaryName: string;

  constructor(scope: Construct, id: string, props: CanaryProps) {
    super(scope, id);
    const { vpc } = props;

    const canary = new synthetics.Canary(this, 'Resource', {
      schedule: synthetics.Schedule.rate(Duration.minutes(1)),
      test: synthetics.Test.custom({
        code: synthetics.Code.fromAsset(join(__dirname, 'canary')),
        handler: 'index.handler',
      }),
      runtime: synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_9_0,
      environmentVariables: {
        BASE_URL: props.targetApiUrl,
      },
      vpc,
      // S3エンドポイントが利用可能なサブネットを優先的に使用
      vpcSubnets: vpc.selectSubnets({
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      }),
    });

    this.canaryName = canary.canaryName;
  }
}
