#!/usr/bin/env bash

# Prompt the user for the secret
read -sp 'Enter your CSP Token: ' CSP_TOKEN
echo

read -sp 'Enter your TMC_URL: ' TMC_URL
echo

read -sp 'Enter your ARIA_LOG_URL: ' ARIA_LOG_URL
echo

# Base64 encode the tokens and urls
ENCODED_CSP_TOKEN=$(echo -n "$CSP_TOKEN" | base64)
ENCODED_TMC_URL=$(echo -n "$TMC_URL" | base64)
ENCODED_ARIA_LOG_URL=$(echo -n "$ARIA_LOG_URL" | base64)

# Create the secret YAML file using a HEREDOC
cat <<EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tmc-audit-logger
  namespace: tmc-audit-logger
type: Opaque
data:
  csp_token: $ENCODED_CSP_TOKEN
  tmc_url: $ENCODED_TMC_URL
  aria_url: $ENCODED_ARIA_LOG_URL
EOF

# Apply the YAML with kubectl
kubectl apply -f secret.yaml

# Delete the YAML file
rm secret.yaml

echo "Secret applied and YAML file removed."
