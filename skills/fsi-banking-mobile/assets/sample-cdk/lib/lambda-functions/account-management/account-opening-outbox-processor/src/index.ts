import { DynamoDBStreamEvent, DynamoDBRecord } from 'aws-lambda';
import { DynamoDBClient, AttributeValue } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, UpdateCommand, PutCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';
import { APIGatewayClient, GetApiKeyCommand } from '@aws-sdk/client-api-gateway';
import { unmarshall } from '@aws-sdk/util-dynamodb';
import { CoreApiClient, SimpleHttpClient, callWithRetry } from '@online-banking/shared';

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

// EventBridgeクライアント
const eventBridgeClient = new EventBridgeClient({
  region: process.env.AWS_REGION || 'ap-northeast-1',
});

// API Gatewayクライアント
const apiGatewayClient = new APIGatewayClient({
  region: process.env.AWS_REGION || 'ap-northeast-1',
});

// Core Banking APIクライアント
const coreApiClient = new CoreApiClient();

// 内部API用HTTPクライアント（認証システム用）
const httpClient = new SimpleHttpClient();

// 環境変数
const ACCOUNT_OPENING_EVENT_STORE_TABLE = process.env.ACCOUNT_OPENING_EVENT_STORE_TABLE || '';
const ACCOUNT_OPENING_OUTBOX_TABLE = process.env.ACCOUNT_OPENING_OUTBOX_TABLE || '';
const EVENT_BUS_NAME = process.env.EVENT_BUS_NAME || '';
const CORE_API_BASE_URL = process.env.CORE_API_BASE_URL || '';
const CORE_API_KEY_ID = process.env.CORE_API_KEY_ID || '';
const CUSTOMER_API_KEY_ID = process.env.CUSTOMER_API_KEY_ID || '';

// Core Banking API レスポンスの型定義
interface CoreBankingAccountResponse {
  success: boolean;
  data?: {
    accountId: string;
    customerId: string;
    accountNumber: string;
    accountType: string;
    balance: number;
    status: string;
  };
  error?: string;
}

// アウトボックスレコードの型定義
interface OutboxRecord {
  id: string;
  timestamp: string;
  aggregateId: string;
  eventType: string;
  status: string;
  payload: {
    applicationId: string;
    transactionId: string;
    customerInfo: any;
    accountType: string;
    action: string;
    accountId?: string;
    accountNumber?: string;
  };
  retryCount: number;
  createdAt: string;
  updatedAt: string;
  processedAt?: string;
  errorMessage?: string;
}

export const handler = async (event: DynamoDBStreamEvent): Promise<void> => {
  console.log('🚀 [DEBUG] Lambda handler started');
  console.log('🚀 [DEBUG] Environment variables:', {
    CORE_API_BASE_URL: CORE_API_BASE_URL || '[NOT SET]',
    CORE_API_KEY_ID: CORE_API_KEY_ID ? '[SET]' : '[NOT SET]',
    BANKING_API_ENDPOINT: process.env.BANKING_API_ENDPOINT || '[NOT SET]',
    EVENT_BUS_NAME: EVENT_BUS_NAME || '[NOT SET]',
    ACCOUNT_OPENING_EVENT_STORE_TABLE: ACCOUNT_OPENING_EVENT_STORE_TABLE || '[NOT SET]',
    ACCOUNT_OPENING_OUTBOX_TABLE: ACCOUNT_OPENING_OUTBOX_TABLE || '[NOT SET]',
  });
  console.log('🚀 [DEBUG] DynamoDB Stream Event received:', {
    recordCount: event.Records.length,
    eventNames: event.Records.map((r) => r.eventName),
  });

  for (const record of event.Records) {
    try {
      console.log(`🚀 [DEBUG] Processing record ${record.eventName}`);
      await processOutboxRecord(record);
      console.log(`✅ [DEBUG] Successfully processed record`);
    } catch (error) {
      console.error('❌ [DEBUG] Error processing record:', error);
      // 個別レコードのエラーは記録するが、他のレコードの処理は継続
    }
  }
  console.log('🚀 [DEBUG] Lambda handler completed');
};

async function processOutboxRecord(record: DynamoDBRecord): Promise<void> {
  console.log('🔍 [DEBUG] processOutboxRecord started');

  if (record.eventName !== 'INSERT' || !record.dynamodb?.NewImage) {
    console.log('🔍 [DEBUG] Skipping non-INSERT event or missing NewImage');
    return;
  }

  const outboxRecord = unmarshall(record.dynamodb.NewImage as Record<string, AttributeValue>) as OutboxRecord;
  console.log('🔍 [DEBUG] Processing outbox record:', {
    id: outboxRecord.id,
    aggregateId: outboxRecord.aggregateId,
    eventType: outboxRecord.eventType,
    status: outboxRecord.status,
    retryCount: outboxRecord.retryCount,
  });

  if (outboxRecord.status !== 'pending') {
    console.log(`🔍 [DEBUG] Skipping record with status: ${outboxRecord.status}`);
    return;
  }

  console.log(`🔍 [DEBUG] Processing action: ${outboxRecord.payload.action}`);

  try {
    // アクションに応じて処理を分岐
    switch (outboxRecord.payload.action) {
      case 'notify_receipt':
        console.log('🔍 [DEBUG] Calling processReceiptNotification');
        await processReceiptNotification(outboxRecord);
        console.log('✅ [DEBUG] processReceiptNotification completed');
        break;
      case 'create_account':
        console.log('🔍 [DEBUG] Calling processAccountCreation');
        await processAccountCreation(outboxRecord);
        console.log('✅ [DEBUG] processAccountCreation completed');
        break;
      default:
        console.warn(`🔍 [DEBUG] Unknown action: ${outboxRecord.payload.action}`);
        await markAsCompleted(outboxRecord);
    }
  } catch (error) {
    console.error(`❌ [DEBUG] Error processing outbox record ${outboxRecord.id}:`, error);
    await markAsFailed(outboxRecord, (error as Error).message);
  }
}

// 受付通知処理
async function processReceiptNotification(outboxRecord: OutboxRecord): Promise<void> {
  console.log(`Processing receipt notification for application: ${outboxRecord.payload.applicationId}`);

  // EventBridgeにイベントを発行
  await publishEvent('AccountOpeningApplicationCreated', {
    applicationId: outboxRecord.payload.applicationId,
    transactionId: outboxRecord.payload.transactionId,
    customerInfo: outboxRecord.payload.customerInfo,
    accountType: outboxRecord.payload.accountType,
    status: 'PENDING',
  });

  // 処理完了をマーク
  await markAsCompleted(outboxRecord);
  console.log(`Receipt notification processed for application: ${outboxRecord.payload.applicationId}`);
}

// 口座作成処理
async function processAccountCreation(outboxRecord: OutboxRecord): Promise<void> {
  console.log(`🏦 [DEBUG] Processing account creation for application: ${outboxRecord.payload.applicationId}`);

  try {
    // 1. Core Banking APIで顧客を作成
    console.log('🏦 [DEBUG] Step 1: Creating customer in Core Banking');
    const customerResult = await createCustomerInCoreBanking(outboxRecord);
    console.log('🏦 [DEBUG] Customer creation result:', JSON.stringify(customerResult, null, 2));

    if (!customerResult.success || !customerResult.data) {
      throw new Error(`Customer creation failed: ${customerResult.error}`);
    }

    // 2. Core Banking APIで口座を作成
    console.log('🏦 [DEBUG] Step 2: Creating account in Core Banking');
    const accountResult = await createAccountInCoreBanking(outboxRecord, customerResult.data.customerId);
    console.log('🏦 [DEBUG] Account creation result:', JSON.stringify(accountResult, null, 2));

    if (!accountResult.success || !accountResult.data) {
      throw new Error(`Account creation failed: ${accountResult.error}`);
    }

    // 3. 認証システムでユーザーを登録
    console.log('🏦 [DEBUG] Step 3: Registering user in Auth System');
    const userResult = await registerUserInAuthSystem(outboxRecord, customerResult.data, accountResult.data);
    console.log(
      '🏦 [DEBUG] User registration result:',
      JSON.stringify({ ...userResult, data: { ...userResult.data, temporaryPassword: '[HIDDEN]' } }, null, 2),
    );

    if (!userResult.success) {
      throw new Error(`User registration failed: ${userResult.error}`);
    }

    // 4. EventStoreに完了イベントを記録
    console.log('🏦 [DEBUG] Step 4: Recording account created event');
    await recordAccountCreatedEvent(outboxRecord, accountResult.data, customerResult.data, userResult.data);
    console.log('🏦 [DEBUG] Account created event recorded');

    // 5. EventBridgeにイベントを発行
    console.log('🏦 [DEBUG] Step 5: Publishing completion event');
    await publishEvent('AccountOpeningApplicationCompleted', {
      applicationId: outboxRecord.payload.applicationId,
      transactionId: outboxRecord.payload.transactionId,
      customerInfo: outboxRecord.payload.customerInfo,
      accountType: outboxRecord.payload.accountType,
      customerId: customerResult.data.customerId,
      accountId: accountResult.data.accountId,
      accountNumber: accountResult.data.accountNumber,
      loginId: userResult.data.loginId,
      status: 'COMPLETED',
    });
    console.log('🏦 [DEBUG] Completion event published');

    // 処理完了をマーク
    console.log('🏦 [DEBUG] Step 6: Marking as completed');
    await markAsCompleted(outboxRecord);
    console.log(`✅ [DEBUG] Account creation completed for application: ${outboxRecord.payload.applicationId}`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorStack = error instanceof Error ? error.stack : undefined;

    console.error(`❌ [DEBUG] Account creation failed for application ${outboxRecord.payload.applicationId}:`, {
      error: errorMessage,
      errorStack: errorStack,
      coreApiBaseUrl: CORE_API_BASE_URL,
      coreApiKeyId: CORE_API_KEY_ID ? '[SET]' : '[NOT SET]',
      bankingApiEndpoint: process.env.BANKING_API_ENDPOINT || '[NOT SET]',
      applicationId: outboxRecord.payload.applicationId,
      retryCount: outboxRecord.retryCount,
      timestamp: new Date().toISOString(),
    });

    // リトライ回数をチェック
    if (outboxRecord.retryCount < 3) {
      await markForRetry(outboxRecord, errorMessage);
    } else {
      await markAsFailed(outboxRecord, errorMessage);
    }
  }
}

// Core Banking APIで顧客作成
async function createCustomerInCoreBanking(outboxRecord: OutboxRecord): Promise<any> {
  const { customerInfo } = outboxRecord.payload;

  const customerRequest = {
    customerInfo: {
      fullName: customerInfo.fullName,
      kana: customerInfo.kana || '',
      email: customerInfo.email,
      phoneNumber: customerInfo.phoneNumber,
      birthdate: customerInfo.birthdate,
      postalCode: customerInfo.postalCode,
      address: customerInfo.address,
      idType: customerInfo.idType,
      idNumber: customerInfo.idNumber,
    },
  };

  console.log('Creating customer in Core Banking for applicationId:', outboxRecord.payload.applicationId);

  try {
    const response = await callWithRetry(async () => {
      console.log('📤 Sending customer creation request for applicationId:', outboxRecord.payload.applicationId);

      return await coreApiClient.createCustomer(customerRequest);
    });

    console.log('Core Banking Customer API response:', response);

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Core Banking Customer API error:', error);
    throw error;
  }
}

// Core Banking APIで口座作成
async function createAccountInCoreBanking(
  outboxRecord: OutboxRecord,
  customerId: string,
): Promise<CoreBankingAccountResponse> {
  const { accountType } = outboxRecord.payload;

  const accountRequest = {
    customerId: customerId,
    accountType: accountType === 'SAVINGS' ? 'SAVINGS' : 'CHECKING',
    initialBalance: 0,
    currency: 'JPY',
  };

  console.log('Creating account in Core Banking:', JSON.stringify(accountRequest, null, 2));

  try {
    const response = await callWithRetry(async () => {
      console.log('📤 Sending account creation request:', { accountRequest });

      return await coreApiClient.createAccount(accountRequest);
    });

    console.log('Core Banking API response:', response);

    // レスポンス形式を統一
    if (response && response.accountId) {
      return {
        success: true,
        data: {
          accountId: response.accountId,
          customerId: response.customerId,
          accountNumber: response.accountNumber, // 新しく追加された口座番号
          accountType: response.accountType,
          balance: response.balance || 0,
          status: response.status || 'ACTIVE',
        },
      };
    } else {
      throw new Error('Invalid response format from Core Banking API');
    }
  } catch (error) {
    console.error('Core Banking API error:', error);
    throw error;
  }
}

// 認証システムでユーザー登録
async function registerUserInAuthSystem(outboxRecord: OutboxRecord, customerData: any, accountData: any): Promise<any> {
  const { customerInfo } = outboxRecord.payload;

  // 一時パスワードを生成
  const temporaryPassword = Math.random().toString(36).slice(-8) + Math.random().toString(36).slice(-8);

  const userRequest = {
    customerId: customerData.customerId,
    accountId: accountData.accountId,
    email: customerInfo.email,
    temporaryPassword: temporaryPassword,
  };

  console.log('Registering user in Auth System for customerId:', userRequest.customerId);

  try {
    // 顧客用API Keyを取得
    const apiKey = await getCustomerApiKey();

    // 内部API呼び出し（同じVPC内）
    const response = await callWithRetry(async () => {
      const baseUrl = (process.env.BANKING_API_ENDPOINT || 'http://localhost:3000').replace(/\/+$/, '');
      const url = `${baseUrl}/api/users/register`;
      console.log('📤 Sending user registration request:', { url });

      return await httpClient.request(url, {
        method: 'POST',
        body: JSON.stringify(userRequest),
        headers: {
          'X-Api-Key': apiKey,
          'Content-Type': 'application/json',
        },
      });
    });

    console.log('Auth System API response:', response.data);

    return {
      success: true,
      data: {
        ...response.data,
        temporaryPassword: temporaryPassword, // メール通知用に保持
      },
    };
  } catch (error) {
    console.error('Auth System API error:', error);
    throw error;
  }
}

// EventStoreに口座作成完了イベントを記録
async function recordAccountCreatedEvent(
  outboxRecord: OutboxRecord,
  accountData: any,
  customerData?: any,
  userData?: any,
): Promise<void> {
  // 最新バージョンを取得するため、既存のイベントを検索
  const existingEvents = (await dynamoDB.send(
    new ScanCommand({
      TableName: ACCOUNT_OPENING_EVENT_STORE_TABLE,
      FilterExpression: 'aggregateId = :aggregateId',
      ExpressionAttributeValues: {
        ':aggregateId': outboxRecord.aggregateId,
      },
    }) as any,
  )) as { Items?: any[] };

  const latestVersion =
    existingEvents.Items && existingEvents.Items.length > 0
      ? Math.max(...existingEvents.Items.map((item: any) => item.version))
      : 0;

  const completedEvent = {
    aggregateId: outboxRecord.aggregateId,
    version: latestVersion + 1,
    type: 'AccountOpeningApplicationCompleted',
    data: {
      id: outboxRecord.payload.applicationId,
      transactionId: outboxRecord.payload.transactionId,
      customerInfo: outboxRecord.payload.customerInfo,
      accountType: outboxRecord.payload.accountType,
      status: 'COMPLETED',
      customerId: customerData?.customerId || accountData.customerId,
      accountId: accountData.accountId,
      accountNumber: accountData.accountNumber, // Core Banking APIから取得した口座番号
      branchCode: accountData.accountNumber?.substring(0, 3) || '001', // 口座番号から支店コードを抽出
      loginId: userData?.loginId, // 認証システムから取得したログインID
      temporaryPassword: userData?.temporaryPassword, // 一時パスワード（メール通知用）
      completedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      receiptNotified: false,
      completionNotified: false,
    },
    metadata: {
      correlationId: outboxRecord.payload.transactionId,
      timestamp: new Date().toISOString(),
      eventVersion: '1.0',
    },
    status: 'completed',
    lastUpdated: new Date().toISOString(),
    processHistory: [
      {
        status: 'account_created',
        timestamp: new Date().toISOString(),
        type: 'core_banking_integration',
        accountId: accountData.accountId,
        accountNumber: accountData.accountNumber,
      },
    ],
  };

  await dynamoDB.send(
    new PutCommand({
      TableName: ACCOUNT_OPENING_EVENT_STORE_TABLE,
      Item: completedEvent,
    }) as any,
  );
}

// EventBridgeイベント発行
async function publishEvent(detailType: string, detail: any): Promise<void> {
  try {
    const params = {
      Entries: [
        {
          Source: 'banking.account-opening',
          DetailType: detailType,
          Detail: JSON.stringify(detail),
          EventBusName: EVENT_BUS_NAME,
        },
      ],
    };

    const result = await eventBridgeClient.send(new PutEventsCommand(params));
    console.log(`Event published: ${detailType}`, result);
  } catch (error) {
    console.error(`Failed to publish event ${detailType}:`, error);
    throw error;
  }
}

// 処理完了をマーク
async function markAsCompleted(outboxRecord: OutboxRecord): Promise<void> {
  console.log(`✅ [DEBUG] Marking outbox record as completed: ${outboxRecord.id}`);
  await dynamoDB.send(
    new UpdateCommand({
      TableName: ACCOUNT_OPENING_OUTBOX_TABLE,
      Key: {
        id: outboxRecord.id,
        timestamp: outboxRecord.timestamp,
      },
      UpdateExpression: 'SET #status = :status, #processedAt = :processedAt, #updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status',
        '#processedAt': 'processedAt',
        '#updatedAt': 'updatedAt',
      },
      ExpressionAttributeValues: {
        ':status': 'completed',
        ':processedAt': new Date().toISOString(),
        ':updatedAt': new Date().toISOString(),
      },
    }) as any,
  );
  console.log(`✅ [DEBUG] Outbox record marked as completed: ${outboxRecord.id}`);
}

// リトライをマーク
async function markForRetry(outboxRecord: OutboxRecord, errorMessage: string): Promise<void> {
  await dynamoDB.send(
    new UpdateCommand({
      TableName: ACCOUNT_OPENING_OUTBOX_TABLE,
      Key: {
        id: outboxRecord.id,
        timestamp: outboxRecord.timestamp,
      },
      UpdateExpression:
        'SET #status = :status, #retryCount = #retryCount + :inc, #errorMessage = :errorMessage, #updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status',
        '#retryCount': 'retryCount',
        '#errorMessage': 'errorMessage',
        '#updatedAt': 'updatedAt',
      },
      ExpressionAttributeValues: {
        ':status': 'pending',
        ':inc': 1,
        ':errorMessage': errorMessage,
        ':updatedAt': new Date().toISOString(),
      },
    }) as any,
  );
}

// 失敗をマーク
async function markAsFailed(outboxRecord: OutboxRecord, errorMessage: string): Promise<void> {
  await dynamoDB.send(
    new UpdateCommand({
      TableName: ACCOUNT_OPENING_OUTBOX_TABLE,
      Key: {
        id: outboxRecord.id,
        timestamp: outboxRecord.timestamp,
      },
      UpdateExpression: 'SET #status = :status, #errorMessage = :errorMessage, #updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status',
        '#errorMessage': 'errorMessage',
        '#updatedAt': 'updatedAt',
      },
      ExpressionAttributeValues: {
        ':status': 'failed',
        ':errorMessage': errorMessage,
        ':updatedAt': new Date().toISOString(),
      },
    }) as any,
  );
}

// 顧客用API Keyを取得
async function getCustomerApiKey(): Promise<string> {
  try {
    const response = await apiGatewayClient.send(
      new GetApiKeyCommand({
        apiKey: CUSTOMER_API_KEY_ID,
        includeValue: true,
      }),
    );

    if (!response.value) {
      throw new Error('API Key value not found');
    }

    return response.value;
  } catch (error) {
    console.error('Failed to get customer API key:', error);
    throw new Error(`Failed to get customer API key: ${error}`);
  }
}
