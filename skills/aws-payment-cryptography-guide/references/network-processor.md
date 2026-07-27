# Network Switches / Payment Processors Guide

## Overview

Network switches and payment processors route transactions between acquirers and
issuers at massive scale. AWS Payment Cryptography provides PIN translation, MAC
verification/generation, and key management without on-premises HSM fleets.

---

## Zone PIN Translation

### Concept

Zone PIN translation is the core cryptographic operation for payment switches. The PIN
block is decrypted under the incoming Zone PIN Key (ZPK) and re-encrypted under the
outgoing ZPK—without ever exposing cleartext PIN.

```
Acquirer → [ZPK-A encrypted PIN] → Switch → [ZPK-I encrypted PIN] → Issuer
```

**API Call: TranslatePinData**

```json
{
  "IncomingWrappedKey": {
    "WrappedKeyMaterial": {
      "Tr31KeyBlock": "<ZPK-A wrapped under KEK-A>"
    }
  },
  "OutgoingWrappedKey": {
    "WrappedKeyMaterial": {
      "Tr31KeyBlock": "<ZPK-I wrapped under KEK-I>"
    }
  },
  "IncomingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "OutgoingTranslationAttributes": {
    "IsoFormat4": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "EncryptedPinBlock": "AC3B4C2E1F5D6A7B"
}
```

### Zone Key Management at Scale

| Challenge | Solution |
|-----------|----------|
| Thousands of ZPK pairs | Key aliases with naming conventions (`alias/zpk-acquirer-{id}-{direction}`) |
| Frequent key rotation | Automate via EventBridge + Lambda triggered by key expiry |
| Key synchronization | Coordinate rotation windows with connected entities |
| Key hierarchy | Maintain KEK relationships per connected entity |

---

## MAC Switching

### Verify-Then-Generate Pattern

```python
import boto3
client = boto3.client('payment-cryptography-data')

def switch_mac(incoming_msg, incoming_mac, incoming_key_id, outgoing_key_id):
    # Step 1: Verify incoming MAC
    try:
        client.verify_mac(
            KeyIdentifier=incoming_key_id,
            MessageData=incoming_msg,
            Mac=incoming_mac,
            VerificationAttributes={'Algorithm': 'ISO9797_ALGORITHM3', 'MacLength': 8}
        )
    except client.exceptions.VerificationFailedException:
        raise Exception("MAC verification failed")
    
    # Step 2: Generate outgoing MAC
    response = client.generate_mac(
        KeyIdentifier=outgoing_key_id,
        MessageData=incoming_msg,
        GenerationAttributes={'Algorithm': 'ISO9797_ALGORITHM3', 'MacLength': 8}
    )
    return response['Mac']
```

### MAC Key Organization

For N connected entities, maintain:
- N inbound MAC keys (one per sender)
- N outbound MAC keys (one per receiver)
- Naming: `alias/mac-{entity-id}-{inbound|outbound}`

---

## High-Throughput Design

### Default Quotas

| Operation | Default TPS | Notes |
|-----------|------------|-------|
| Symmetric operations | 500 | TranslatePinData, GenerateMac, VerifyMac |
| Asymmetric operations | 50 | RSA operations |
| Control plane | 10 | CreateKey, DeleteKey |

### Horizontal Scaling Across Regions

```
              ┌──────────────┬──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼─────┐  ┌────▼────────┐
     │ us-east-1  │  │ eu-west-1  │  │ ap-north-1  │
     │  500 TPS   │  │  500 TPS   │  │  500 TPS    │
     └────────────┘  └────────────┘  └─────────────┘
                   Total: 1,500 TPS
```

### Latency Optimization

- **VPC Endpoints**: PrivateLink to eliminate internet hops
- **Connection pooling**: Reuse HTTPS connections (keep-alive)
- **Regional affinity**: Route transactions to nearest region
- **Payload minimization**: Send only required fields

```python
from botocore.config import Config
config = Config(
    max_pool_connections=50,
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 2, 'mode': 'adaptive'}
)
client = boto3.client('payment-cryptography-data', config=config)
```

---

## Multi-Region Architecture

### Active-Active Deployment with Multi-Region Keys

```
Region A (Primary)                    Region B (Secondary)
┌──────────────────────┐             ┌──────────────────────┐
│  APC Endpoint        │             │  APC Endpoint        │
│  MRK: mrk-abc123    │◄───sync────►│  MRK: mrk-abc123    │
│  (same key material) │             │  (same key material) │
└──────────────────────┘             └──────────────────────┘
```

### Failover Design

1. **Health checks**: Monitor APC endpoints per region via CloudWatch
2. **Automatic failover**: Route 53 health-based routing switches traffic
3. **Key availability**: MRKs are designed to maintain cryptographic continuity during failover
4. **State management**: Transaction state in DynamoDB Global Tables

### Data Sovereignty

- Use single-region keys where data sovereignty mandates apply
- Document key residency requirements per connected entity
- Consider separate key hierarchies for regulated vs. non-regulated traffic

---

## Large-Scale Key Management

### Scale Profile

A switch with 500 connections maintains **~2,000+ active keys**:
- 1 ZPK pair per acquirer/issuer connection
- 1 MAC key pair per connected entity
- 1 KEK per connected entity

### Key Rotation Automation

```python
import boto3, json
events = boto3.client('events')

def schedule_key_rotation(key_alias, rotation_days=90):
    rule_name = f"key-rotation-{key_alias.replace('/', '-')}"
    events.put_rule(
        Name=rule_name,
        ScheduleExpression=f"rate({rotation_days} days)",
        State='ENABLED'
    )
    events.put_targets(Rule=rule_name, Targets=[{
        'Id': 'rotation-handler',
        'Arn': 'arn:aws:lambda:region:account:function:key-rotator',
        'Input': json.dumps({'key_alias': key_alias})
    }])
```

### Alias Management & Key Lifecycle

```
alias/zpk-{entity_type}-{entity_id}-{direction}-{version}
  Examples: alias/zpk-acquirer-visa-inbound-v2
            alias/mac-processor-fiserv-inbound-v3
```

| Phase | Action | Automation |
|-------|--------|-----------|
| Generation | Create key with attributes | Lambda + Step Functions |
| Distribution | Exchange via TR-31 blocks | Secure API / SFTP |
| Activation | Update alias to new key | Coordinated cutover |
| Rotation | Generate replacement, swap | EventBridge scheduled |
| Deactivation | Remove alias, disable | Grace period (24-48h) |
| Deletion | Schedule (7-day wait) | Compliance-driven |

---

## Throttling Mitigation

### Retry with Exponential Backoff

```python
import time, random
from botocore.exceptions import ClientError

def call_with_retry(func, max_retries=5, base_delay=0.1):
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                time.sleep(random.uniform(0, delay))
            else:
                raise
```

### Quota Monitoring via CloudWatch

**Key Metrics:**
- `ThrottledRequests` — approaching quota limits
- `SuccessfulRequests` — baseline transaction volume
- `Latency` (p50, p99) — performance degradation signals

**Pre-warming tips:** Gradually ramp traffic for new regions; avoid sudden bursts
after maintenance; distribute key operations across time windows.

---

## Summary

| Capability | APC Feature | Scale Consideration |
|-----------|-------------|---------------------|
| PIN Translation | TranslatePinData | 500 TPS default, multi-region |
| MAC Switching | VerifyMac + GenerateMac | Dual-call per transaction |
| Key Management | Aliases + TR-31 | Thousands of keys, automated lifecycle |
| High Availability | Multi-Region Keys | Active-active with failover |
