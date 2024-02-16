# Overview

This is a super-simple Proof-of-Concept to forward event logs from TMC's event stream to Aria Operations for Logs. It consists of two containers running in a single pod. It leverages the vmware-log-intelligence plugin for fluentd to forward logs to AOFL. Reading from TMC's API is a simple python script.  

Here's a logical diagram:

```

     ┌─────────────────────────┐
     │TMC Audit/Event Log      │
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
     ┌─▼───────────────────────────────────────────────┐
     │ Aria Operations for Logs                        │
     │                                                 │
     │  /v1/streams/ingestion-pipeline-stream (SaaS)   │
     │                                                 │
     │                  or                             │  
     │                                                 │
     │              Host:9543 (Self-Managed            │
     │                                                 │
     │                                                 │
     └─────────────────────────────────────────────────┘


```


# Installation

Instructions are for either SaaS or SM (Self-Managed) installs of AOfL.

## SaaS

If you're using the SaaS Aria Operations for Logs, you'll need:

* A Kubernetes cluster to run this on
* Your CSP (Cloud Service Portal) token
* Your TMC (Tanzu Mission Control) URL
* Your Aria Operations for Logs token
* Your Aria Operations for Logs ingestion pipeline URL

## Self-Managed 

If you're using the Self-Managed Aria Operations for Logs, you'll need:

* A Kubernetes cluster to run this on
* Your CSP (Cloud Service Portal) token
* Your TMC (Tanzu Mission Control) URL
* Your Aria Operations for Logs hostname or URL

### Setup

Create the namespace on your cluster:

Run the `install.sh` shell script:

It's a good idea to have everything in the "Things you're going to need" section above ready to go. The script will prompt you for the type of install and the secrets that you'll need:

Self-Managed example:

```text
❯ ./install.sh 
Please select an option:
1) self-managed
2) saas
Enter the number of your choice: 1
namespace/tmc-audit-logger created
Enter your CSP Token: 
Enter your TMC_URL: 
Enter your ARIA_LOG_URL: 
secret/tmc-audit-logger created
Secret applied and YAML file removed.
deployment.apps/tmc-audit-logger-deployment created
configmap/fluentd-config created
```

SaaS example:

```text
❯ ./install.sh 
Please select an option:
1) self-managed
2) saas
Enter the number of your choice: 2
namespace/tmc-audit-logger created
Enter your CSP Token: 
Enter your TMC_URL: 
Enter your ARIA_LOG_TOKEN: 
Enter your ARIA_LOG_URL: 
secret/tmc-audit-logger created
Secret applied and YAML file removed.
deployment.apps/tmc-audit-logger-deployment created
configmap/fluentd-config created
```

### Validate

Look for your deployment in the `tmc-audit-logger` namespace. 

```text
kubectl get deploy -n tmc-audit-logger 
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
tmc-audit-logger-deployment   1/1     1            1           2d19h
```

```text
kubectl get pods -n tmc-audit-logger   
NAME                                          READY   STATUS    RESTARTS   AGE
tmc-audit-logger-deployment-64b76d599-r2zqq   2/2     Running   0          2d19h
```

There's two containers, `fluentd` and `tmcreader`. The `tmcreader` container is responsible for reading events off of TMC, and the `fluentd` container is responsible for syndicating those events into AOFL.

Tail the logs from either container to verify everything is working. You should also see logs appear in the AOFL UI.

##### tmcreader

You should see some events like the following:

```text
kubectl logs po/tmc-audit-logger-deployment-64b76d599-r2zqq -n tmc-audit-logger -c tmcreader | tail
2024-02-16T14:39:03: INFO: Read: {"result":{"event":{"id":"433946f0-ca32-45fb-bd4c-c559b86a1db8","time":"2024-02-16T14:39:01.344949827Z","type":"com.vmware.tmc.audit","source":"some-api","subject":"username","attributes":{"level":"Info","orgid":"r3d4c73d-r3d4c73dr3d4c73d","userid":"banana.tld:r3d4c73d-r3d4c73dr3d4c73d"},"data":{"ClientInfo":{"ClientName":"","ClientPlatform":"","ClientVersion":""},"ExtraInfo":null,"GRPC":{"Code":"Canceled","Method":"Stream","Service":"vmware.tanzu.manage.v1alpha1.events.Events"},"HTTP":{"Code":"","Method":"","Service":""},"IdentityInfo":{"AgentID":"","OperatorID":"","OperatorOrgID":"","ServiceID":"","UserEmail":"fake@banana.tld","UserID":"banana.tld:r3d4c73d-r3d4c73dr3d4c73d","UserName":"fake"},"OrgID":"r3d4c73d-r3d4c73dr3d4c73d","RequestID":"r3d4c73dr3d4c73dr3d4c73d","State":"Events_Service - Stream - Request_rejected","Timestamp":"2024-02-16T14:39:01.344884886Z"}}}}
```

##### fluentd

You should see some indication that the events are being copied into AOFL: (here, the `http_conn_debug` parameter is set to `true` in the `vmware_loginsight` fluentd plugin, it's probably a good idea for troubleshooting or validating your setup is working to set this).

```text
kubectl logs po/tmc-audit-logger-deployment-64b76d599-r2zqq -n tmc-audit-logger -c fluentd | tail 
-> "Date: Fri, 16 Feb 2024 14:41:30 UTC\r\n"
-> "X-LI-Build: 22806512\r\n"
-> "ACCESS-CONTROL-EXPOSE-HEADERS: X-LI-Build\r\n"
-> "content-length: 56\r\n"
-> "Content-Type: application/json\r\n"
-> "\r\n"
reading 56 bytes...
-> "{\"status\":\"ok\",\"message\":\"events ingested\",\"ingested\":1}"
read 56 bytes
Conn keep-alive

```

