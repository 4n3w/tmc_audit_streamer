# Overview

This is a super-simple Proof-of-Concept to forward event logs from TMC's event stream to Aria Operations for Logs. It consists of two containers running in a single pod. It leverages the vmware-log-intelligence plugin for fluentd to forward logs to AOFL. Reading from TMC's API is a simple python script.  

Here's a logical diagram:

```

     ┌─────────────────────────┐
     │TMC Audit Log            │
     │                         │
 ┌───┤ /v1alpha1/events/stream │
 │   │                         │
 │   │                         │
 │   └─────────────────────────┘
 │
 │   ┌─────────────────────────────────────────┐
 │   │ Log Forwarding Pod (in a K8S cluster)   │
 │   │  ┌────────────────┐  ┌────────────────┐ │
 │   │  │Container       │  │Container       │ │
 │   │  │                │  │                ├─┼─┐
 └───┴──►    python      │  │    fluentd     │ │ │
   reads│                │  │                │ │ │
     │  └────┬───────────┘  └──────────▲─────┘ │ │
     │       │                         │       │ │
     │       │writes                   │       │ │
     │       │                         │       │ │
     │       │  ┌───────────────────┐  │       │ │
     │       │  │ volumeMounts      │  │reads  │ │
     │       └──►- name: shared-logs├──┘       │ │
     │          │  mountPath: /tmc  │          │ │
     │          └───────────────────┘          │ │
     │                                         │ │
     └─────────────────────────────────────────┘ │
                                                 │
       ┌─────────────────────────────────────────┘
       │ writes
       │
     ┌─▼───────────────────────────────────────┐
     │ Aria Operations for Logs                │
     │                                         │
     │  /v1/streams/ingestion-pipeline-stream  │
     │                                         │
     └─────────────────────────────────────────┘


```


# Installation

Things you're going to need:
* A Kubernetes cluster to run this on
* Your CSP (Cloud Service Portal) token
* Your Aria Operations for Logs token
* Your TMC (Tanzu Mission Control) URL
* Your Aria Operations for Logs ingestion pipeline URL

## Kubernetes Setup

Create the namespace on your cluster:

```shell
  cd kubernetes
  kubectl apply -f namespace.yaml
```

Create the secrets -- it's a good idea to have everything in the "Things you're going to need" section above ready to go. The `secret.sh` shell script will prompt you for:

1. Your CSP Token
2. Your TMC_URL
3. Your ARIA_LOG_TOKEN
4. Your ARIA_LOG_URL

Run the secret.sh script; after prompting you for your secrets, it will create a temporary `secret.yaml` file, and apply it to your cluster with `kubectl`, and it should remove the `secret.yaml` file.

```shell
./secret.sh
```

Almost there, you'll need to create a `configmap` from the `fluent.conf` file. It's a good idea to understand how this `fluent.conf` file is configured, especially if you want to do more advanced filtering. The `fluent-nostdoutecho.conf` is an alternative, nearly identical configuration file to `fluent.conf`, however it does not echo the log lines it receives from the python script running in the   

```shell
kubectl create configmap fluentd-config --from-file=fluent.conf
kubectl apply -f deployment.yaml
```

Tail the logs from either container to verify everything is working. You should also see logs appear in the AOFL UI.
