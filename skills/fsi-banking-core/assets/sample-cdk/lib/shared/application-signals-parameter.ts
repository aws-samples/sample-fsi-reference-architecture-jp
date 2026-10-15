import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

/**
 * Application Signals用のデフォルト設定JSON
 * CloudWatch Application Signalsの標準的な設定を提供
 */
const DEFAULT_APPLICATION_SIGNALS_CONFIG = {
  agent: {
    config: {
      logs: {
        logs_collected: {
          application_signals: {},
        },
      },
      traces: {
        traces_collected: {
          application_signals: {},
        },
      },
      metrics: {
        metrics_collected: {
          application_signals: {},
        },
      },
    },
  },
};

/**
 * Application Signals用のSSMパラメータを作成する
 *
 * この関数は以下の機能を提供します：
 * - 新規環境でのSSMパラメータ自動作成
 * - 既存パラメータがある場合は値を更新
 * - デフォルト設定の提供
 *
 * CDKの標準動作により、以下のように処理されます：
 * - 既存パラメータがない場合：新規作成
 * - 既存パラメータがある場合：値を比較して必要に応じて更新
 * - 同じ値の場合：変更なし
 *
 * @param scope - CDKコンストラクトのスコープ
 * @param id - コンストラクトID（一意である必要があります）
 * @param parameterName - SSMパラメータ名（オプション、デフォルトは標準名）
 * @returns 作成されたStringParameterインスタンス
 */
export function createApplicationSignalsParameter(
  scope: Construct,
  id = 'ApplicationSignalsConfig',
  parameterName = '/ecs/cloudwatch-agent/application-signals-config',
): StringParameter {
  // CDKの標準動作に任せる
  // 既存パラメータがある場合は自動的に適切に処理される
  const parameter = new StringParameter(scope, id, {
    parameterName,
    stringValue: JSON.stringify(DEFAULT_APPLICATION_SIGNALS_CONFIG),
    description: 'CloudWatch Application Signals configuration for ECS tasks',
    // パラメータの階層を考慮してStandardTierを使用
    tier: undefined, // デフォルトのStandardTierを使用
  });

  return parameter;
}

/**
 * 既存のApplication Signals SSMパラメータを参照する
 *
 * @param scope - CDKコンストラクトのスコープ
 * @param id - コンストラクトID
 * @param parameterName - SSMパラメータ名（オプション、デフォルトは標準名）
 * @returns 参照されたIStringParameterインスタンス
 */
export function referenceApplicationSignalsParameter(
  scope: Construct,
  id = 'ApplicationSignalsConfigRef',
  parameterName = '/ecs/cloudwatch-agent/application-signals-config',
) {
  return StringParameter.fromStringParameterName(scope, id, parameterName);
}

/**
 * Application Signals設定のデフォルト値を取得
 *
 * @returns デフォルトのApplication Signals設定オブジェクト
 */
export function getDefaultApplicationSignalsConfig(): object {
  return DEFAULT_APPLICATION_SIGNALS_CONFIG;
}
