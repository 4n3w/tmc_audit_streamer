kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml
kubectl create configmap fluentd-config --from-file=fluent.conf
kubectl apply -f deployment.yaml
