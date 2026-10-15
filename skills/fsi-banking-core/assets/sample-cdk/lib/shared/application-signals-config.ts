import { Construct } from 'constructs';
import { aws_ssm as ssm } from 'aws-cdk-lib';
import { RemovalPolicy } from 'aws-cdk-lib';

/**
 * CloudWatch Application Signals 用の SSM パラメータ設定
 *
 * この構成要素は以下の機能を提供します：
 * - CloudWatch Agent 用の Application Signals 設定を含む SSM パラメータの作成
 * - AWS 公式ドキュメントに記載されている正確な JSON 設定の使用
 * - ECS タスク定義が参照する前にパラメータが存在することを保証
 *
 * 参考: https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-ECS-Sidecar.html
 */

export interface ApplicationSignalsConfigProps {
  /**
   * パラメータ命名用の環境名
   */
  envName: string;

  /**
   * リージョン固有設定用の AWS リージョン
   */
  region: string;

  /**
   * パラメータ更新を許可するかどうか (デフォルト: false)
   */
  allowUpdates?: boolean;
}

export class ApplicationSignalsConfig extends Construct {
  public readonly parameter: ssm.StringParameter;
  public readonly parameterName: string;

  constructor(scope: Construct, id: string, props: ApplicationSignalsConfigProps) {
    super(scope, id);

    const { envName, region, allowUpdates = false } = props;

    // パラメータ名を定義
    // 既存のコードで参照されている名前と一致させる
    this.parameterName = '/ecs/cloudwatch-agent/application-signals-config';

    // AWS 公式ドキュメント (ステップ3) に記載されている正確な JSON 設定
    // https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-ECS-Sidecar.html
    const configJson = {
      traces: {
        traces_collected: {
          application_signals: {},
        },
      },
      logs: {
        metrics_collected: {
          application_signals: {},
        },
      },
    };

    // SSM パラメータを作成
    this.parameter = new ssm.StringParameter(this, 'Parameter', {
      parameterName: this.parameterName,
      description: `CloudWatch Agent configuration for Application Signals in Core Banking Sample (${envName}, ${region})`,
      stringValue: JSON.stringify(configJson),
      tier: ssm.ParameterTier.STANDARD,
    });

    // CDK スタックが破棄される際にパラメータも削除
    this.parameter.applyRemovalPolicy(RemovalPolicy.DESTROY);
  }
}
