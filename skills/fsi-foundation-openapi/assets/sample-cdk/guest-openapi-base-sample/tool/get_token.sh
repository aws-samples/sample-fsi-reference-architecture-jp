#!/bin/bash

#Cognito UserID and Password
export USER='xxxxx@xxxx.xxx'
export PASSWORD='xxxxxxxx'

#Cognito User pool ID and Client ID from AWS Management Console
export POOLID='ap-northeast-1_xxxxxxxx'
export CLIENTID='xxxxxxxxxxxxxxxxxxxx'

#API URL (CloudFront DomainName + /test)
export URL='https://xxxxxx.xxxxx.xxx/test'

# Security: this is a verification-only helper. Variables are quoted to avoid
# word-splitting, and the ID token is NOT echoed to stdout (shell history / CI
# logs / terminals can leak it). The token is exported so a caller that sources
# this script can use "$TOKEN". `--permanent` is a convenience for verification;
# for production use a temporary password flow instead.

#Set User Password by admin
aws cognito-idp admin-set-user-password --user-pool-id "$POOLID" --username "$USER" --password "$PASSWORD" --permanent

#Get ID Token from Cognito
export TOKEN=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id "$CLIENTID" --auth-parameter "USERNAME=$USER,PASSWORD=$PASSWORD" | grep IdToken | awk '{print $2}')

#Confirm retrieval without printing the token itself
if [ -n "$TOKEN" ]; then
  echo "ID Token retrieved (not printed). It is available as \$TOKEN in the current shell if this script was sourced."
else
  echo "Failed to retrieve ID Token." >&2
fi

