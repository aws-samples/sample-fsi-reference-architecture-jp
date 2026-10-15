import { EventBridgeEvent } from 'aws-lambda';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, UpdateCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';
import { SimpleHttpClient, callWithRetry } from '@online-banking/shared';

// DynamoDBクライアント
const dynamoClient = new DynamoDBClient({
  region: process.env.AWS_REGION || 'ap-northeast-1',
});
const dynamoDB = DynamoDBDocumentClient.from(dynamoClient, {
  marshallOptions: {
    convertEmptyValues: false,
    removeUndefinedValues: true,
    convertClassInstanceToMap: false,
  },
  unmarshallOptions: {
    wrapNumbers: false,
  },
});

// HTTPクライアント
const httpClient = new SimpleHttpClient();

// 環境変数
const ACCOUNT_OPENING_EVENT_STORE_TABLE = process.env.ACCOUNT_OPENING_EVENT_STORE_TABLE || '';
const MAIL_DELIVERY_API = process.env.MAIL_DELIVERY_API || '';
const MAIL_DELIVERY_API_KEY = process.env.MAIL_DELIVERY_API_KEY || '';

// イベント詳細の型定義
interface AccountOpeningEventDetail {
  applicationId: string;
  transactionId: string;
  customerInfo: {
    fullName: string;
    email: string;
    phoneNumber: string;
  };
  accountType: string;
  status: string;
  customerId?: string;
  accountId?: string;
  accountNumber?: string;
  loginId?: string;
}

// メール送信リクエストの型定義
interface EmailRequest {
  recipients: {
    email: string;
    name?: string;
    type: 'to' | 'cc' | 'bcc';
  }[];
  subject: string;
  body: string;
  sender?: {
    email: string;
    name?: string;
  };
  priority?: 'high' | 'normal' | 'low';
  tags?: string[];
}

export const handler = async (event: EventBridgeEvent<string, AccountOpeningEventDetail>): Promise<void> => {
  console.log('Event received:', JSON.stringify(event, null, 2));

  try {
    const { detail, 'detail-type': detailType } = event;
    const { applicationId, customerInfo } = detail;

    console.log(`Processing ${detailType} event for application ${applicationId}`);

    // イベントタイプに応じて処理を分岐
    if (detailType === 'AccountOpeningApplicationCreated') {
      await sendReceiptEmail(detail);
    } else if (detailType === 'AccountOpeningApplicationCompleted') {
      await sendCompletionEmail(detail);
    }

    console.log(`Successfully processed ${detailType} event for application ${applicationId}`);
  } catch (error) {
    console.error('Error processing event:', error);
    throw error;
  }
};

// 申込受付メール送信
async function sendReceiptEmail(detail: AccountOpeningEventDetail): Promise<void> {
  console.log(`Sending receipt email for application: ${detail.applicationId}`);

  try {
    // 既に送信済みかチェック
    const isAlreadySent = await checkNotificationStatus(detail.applicationId, 'receiptNotified');
    if (isAlreadySent) {
      console.log(`Receipt notification already sent for ${detail.applicationId}`);
      return;
    }

    const emailRequest: EmailRequest = {
      recipients: [
        {
          email: detail.customerInfo.email,
          name: detail.customerInfo.fullName,
          type: 'to',
        },
      ],
      subject: '【サンプル銀行】口座開設申込受付のお知らせ',
      body: `${detail.customerInfo.fullName} 様

サンプル銀行をご利用いただきありがとうございます。
口座開設のお申込みを受け付けました。

申込ID: ${detail.applicationId}
申込日時: ${new Date().toLocaleString('ja-JP')}

審査完了後、改めてご連絡いたします。
ご不明な点がございましたら、お気軽にお問い合わせください。

サンプル銀行`,
      sender: {
        email: process.env.SENDER_EMAIL || 'noreply@example.com',
        name: 'AWS銀行',
      },
      priority: 'normal',
      tags: ['account-opening', 'receipt'],
    };

    // メール配信処理
    console.log(
      '📧 メール配信基盤はこのサンプルアーキテクチャの対象外ですが、このLambdaから呼び出す形を想定して設計しています',
    );
    console.log('📧 実装時は以下のような外部API呼び出しを行います:', {
      recipient: detail.customerInfo.email,
      subject: emailRequest.subject,
      template: 'account-opening-receipt',
    });

    // 送信済みフラグを更新
    await updateNotificationStatus(detail.applicationId, 'receiptNotified', true);

    console.log(`Receipt notification processed for ${detail.applicationId}`);
  } catch (error) {
    console.error('Error sending receipt email:', error);
    throw error;
  }
}

// 口座開設完了メール送信
async function sendCompletionEmail(detail: AccountOpeningEventDetail): Promise<void> {
  console.log(`Sending completion email for application: ${detail.applicationId}`);

  try {
    // 既に送信済みかチェック
    const isAlreadySent = await checkNotificationStatus(detail.applicationId, 'completionNotified');
    if (isAlreadySent) {
      console.log(`Completion notification already sent for ${detail.applicationId}`);
      return;
    }

    // Core Banking APIで作成された口座番号を使用
    const accountNumber = detail.accountNumber || '口座番号未設定';
    const branchCode = accountNumber.substring(0, 3) || '001';
    const accountNumberFormatted = accountNumber ? `${branchCode}-${accountNumber.substring(3)}` : '口座番号未設定';
    const loginId = detail.loginId || 'ログインID未設定';

    const emailRequest: EmailRequest = {
      recipients: [
        {
          email: detail.customerInfo.email,
          name: detail.customerInfo.fullName,
          type: 'to',
        },
      ],
      subject: '【サンプル銀行】口座開設完了のお知らせ',
      body: `${detail.customerInfo.fullName} 様

サンプル銀行をご利用いただきありがとうございます。
口座開設が完了しました。

口座番号: ${accountNumberFormatted}
口座種別: ${detail.accountType === 'SAVINGS' ? '普通預金' : '当座預金'}
開設日: ${new Date().toLocaleDateString('ja-JP')}

【オンラインバンキングのご案内】
当行のオンラインバンキングサービスをぜひご利用ください。

ログインID: ${loginId}
初回ログイン時は、メールアドレスに送信される一時パスワードをご利用ください。
ログイン後、必ずパスワードを変更してください。

オンラインバンキングURL: https://banking.example.com/login

今後ともサンプル銀行をよろしくお願いいたします。

サンプル銀行`,
      sender: {
        email: process.env.SENDER_EMAIL || 'noreply@example.com',
        name: 'サンプル銀行',
      },
      priority: 'normal',
      tags: ['account-opening', 'completion'],
    };

    // メール配信処理
    console.log(
      '📧 メール配信基盤はこのサンプルアーキテクチャの対象外ですが、このLambdaから呼び出す形を想定して設計しています',
    );
    console.log('📧 実装時は以下のような外部API呼び出しを行います:', {
      recipient: detail.customerInfo.email,
      subject: emailRequest.subject,
      template: 'account-opening-completion',
    });

    // 送信済みフラグを更新
    await updateNotificationStatus(detail.applicationId, 'completionNotified', true);

    console.log(`Completion notification processed for ${detail.applicationId}`);
  } catch (error) {
    console.error('Error sending completion email:', error);
    throw error;
  }
}

// メール配信API呼び出し関数（サンプル実装）
// 実際の実装では、自社のメール配信基盤に合わせてカスタマイズしてください
async function sendEmailViaAPI(emailRequest: EmailRequest): Promise<void> {
  console.log('📧 メール配信基盤への接続処理（サンプル実装）');
  console.log('📧 実装時は自社のメール配信システムに合わせてカスタマイズしてください:', {
    apiEndpoint: MAIL_DELIVERY_API,
    recipients: emailRequest.recipients.map((r) => r.email),
    subject: emailRequest.subject,
  });
}

// 通知状態をチェック
async function checkNotificationStatus(applicationId: string, field: string): Promise<boolean> {
  try {
    const result = (await dynamoDB.send(
      new ScanCommand({
        TableName: ACCOUNT_OPENING_EVENT_STORE_TABLE,
        FilterExpression: 'aggregateId = :aggregateId',
        ExpressionAttributeValues: {
          ':aggregateId': applicationId,
        },
      }) as any,
    )) as { Items?: any[] };

    if (!result.Items || result.Items.length === 0) {
      return false;
    }

    // 最新バージョンのイベントを取得
    const latestEvent = result.Items.sort((a: any, b: any) => b.version - a.version)[0];
    return latestEvent.data?.[field] || false;
  } catch (error) {
    console.error(`Error checking notification status: ${error}`);
    return false;
  }
}

// 通知状態を更新
async function updateNotificationStatus(applicationId: string, field: string, value: boolean): Promise<void> {
  try {
    // 最新のイベントを取得
    const result = (await dynamoDB.send(
      new ScanCommand({
        TableName: ACCOUNT_OPENING_EVENT_STORE_TABLE,
        FilterExpression: 'aggregateId = :aggregateId',
        ExpressionAttributeValues: {
          ':aggregateId': applicationId,
        },
      }) as any,
    )) as { Items?: any[] };

    if (!result.Items || result.Items.length === 0) {
      throw new Error(`Application not found: ${applicationId}`);
    }

    const latestEvent = result.Items.sort((a: any, b: any) => b.version - a.version)[0];

    // 通知状態を更新したイベントを作成
    const updatedData = {
      ...latestEvent.data,
      [field]: value,
      [`${field}At`]: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const notificationEvent = {
      aggregateId: applicationId,
      version: latestEvent.version + 1,
      type: `AccountOpeningNotification${field.charAt(0).toUpperCase() + field.slice(1)}`,
      data: updatedData,
      metadata: {
        correlationId: latestEvent.metadata.correlationId,
        timestamp: new Date().toISOString(),
        eventVersion: '1.0',
      },
      status: 'completed',
      lastUpdated: new Date().toISOString(),
      processHistory: [
        ...latestEvent.processHistory,
        {
          status: 'notification_sent',
          timestamp: new Date().toISOString(),
          type: field,
        },
      ],
    };

    await dynamoDB.send(
      new UpdateCommand({
        TableName: ACCOUNT_OPENING_EVENT_STORE_TABLE,
        Key: {
          aggregateId: applicationId,
          version: latestEvent.version + 1,
        },
        UpdateExpression:
          'SET #type = :type, #data = :data, #metadata = :metadata, #status = :status, #lastUpdated = :lastUpdated, #processHistory = :processHistory',
        ExpressionAttributeNames: {
          '#type': 'type',
          '#data': 'data',
          '#metadata': 'metadata',
          '#status': 'status',
          '#lastUpdated': 'lastUpdated',
          '#processHistory': 'processHistory',
        },
        ExpressionAttributeValues: {
          ':type': notificationEvent.type,
          ':data': notificationEvent.data,
          ':metadata': notificationEvent.metadata,
          ':status': notificationEvent.status,
          ':lastUpdated': notificationEvent.lastUpdated,
          ':processHistory': notificationEvent.processHistory,
        },
      }) as any,
    );

    console.log(`Notification status updated: ${field} = ${value}`);
  } catch (error) {
    console.error(`Error updating notification status: ${error}`);
    throw error;
  }
}
