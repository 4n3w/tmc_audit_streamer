#!/usr/bin/env bash

echo "Please select an option:"
echo "1) self-managed"
echo "2) saas"
read -p "Enter the number of your choice: " choice

deploymenttype=""

case $choice in
  1) deploymenttype="self-managed";;
  2) deploymenttype="saas";;
  *) echo "Invalid choice"; exit 1;;
esac

kubectl apply -f namespace.yaml
pushd $deploymenttype
./secret.sh
kubectl apply -f deployment.yaml
popd
