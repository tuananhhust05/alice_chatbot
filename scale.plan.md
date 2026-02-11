# Alice Chatbot - Kubernetes Scaling Plan

## Executive Summary

This document outlines the scaling strategy for Alice Chatbot using Kubernetes (K8s). The core principle is **microservice decomposition** - each service is independently scalable and only needs to expose a common endpoint for other nodes in the system to connect.

---

## 1. Architecture Overview

### 1.1 Current Services

| Service | Type | Port | Scaling Priority |
|---------|------|------|------------------|
| Frontend | React App | 3000 | Medium |
| Backend | FastAPI | 8000 | High |
| Orchestrator | FastAPI | 8001 | High |
| Dataflow | Python | 8002 | Medium |
| MongoDB | Database | 27017 | High |
| Weaviate | Vector DB | 8080 | Medium |
| Redis | Cache | 6379 | High |
| Kafka | Message Queue | 9092 | High |
| Kafkaflow | Message Queue | 9094 | Medium |

### 1.2 Scaling Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Node 1     │    │   Node 2     │    │   Node 3     │       │
│  │              │    │              │    │              │       │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │       │
│  │ │ Backend  │ │    │ │ Backend  │ │    │ │ Backend  │ │       │
│  │ │ Pod 1    │ │    │ │ Pod 2    │ │    │ │ Pod 3    │ │       │
│  │ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                              │                                   │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │  K8s Service     │                         │
│                    │  (LoadBalancer)  │                         │
│                    │  backend:8000    │                         │
│                    └──────────────────┘                         │
│                              │                                   │
│                    Unified Endpoint                              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Concept**: Each service exposes a single K8s Service endpoint. Other services connect to this unified endpoint, while K8s handles load balancing across multiple pods.

---

## 2. Kubernetes Resource Definitions

### 2.1 Backend Service

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: alice-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alice-backend
  template:
    metadata:
      labels:
        app: alice-backend
    spec:
      containers:
      - name: backend
        image: alice/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: alice-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### 2.2 Orchestrator Service

```yaml
# orchestrator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
  labels:
    app: alice-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alice-orchestrator
  template:
    metadata:
      labels:
        app: alice-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: alice/orchestrator:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: orchestrator-config
        - secretRef:
            name: orchestrator-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator
spec:
  selector:
    app: alice-orchestrator
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

### 2.3 Redis Cluster

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    app: alice-redis
spec:
  replicas: 1  # Use Redis Sentinel/Cluster for HA
  selector:
    matchLabels:
      app: alice-redis
  template:
    metadata:
      labels:
        app: alice-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: alice-redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### 2.4 Kafka Cluster

```yaml
# kafka-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  labels:
    app: alice-kafka
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: alice-kafka
  template:
    metadata:
      labels:
        app: alice-kafka
    spec:
      containers:
      - name: kafka
        image: apache/kafka:latest
        ports:
        - containerPort: 9092
          name: client
        - containerPort: 9093
          name: controller
        env:
        - name: KAFKA_NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: KAFKA_PROCESS_ROLES
          value: "controller,broker"
        - name: KAFKA_LISTENERS
          value: "PLAINTEXT://:9092,CONTROLLER://:9093"
        - name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP
          value: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT"
        - name: KAFKA_CONTROLLER_QUORUM_VOTERS
          value: "0@kafka-0:9093,1@kafka-1:9093,2@kafka-2:9093"
        - name: KAFKA_CONTROLLER_LISTENER_NAMES
          value: "CONTROLLER"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka
  volumeClaimTemplates:
  - metadata:
      name: kafka-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
spec:
  selector:
    app: alice-kafka
  ports:
  - port: 9092
    targetPort: 9092
    name: client
  type: ClusterIP
```

### 2.5 MongoDB Replica Set

```yaml
# mongodb-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  labels:
    app: alice-mongodb
spec:
  serviceName: mongodb
  replicas: 3
  selector:
    matchLabels:
      app: alice-mongodb
  template:
    metadata:
      labels:
        app: alice-mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongodb-secrets
              key: username
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secrets
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: mongo-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongo-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
spec:
  selector:
    app: alice-mongodb
  ports:
  - port: 27017
    targetPort: 27017
  type: ClusterIP
```

---

## 3. Horizontal Pod Autoscaler (HPA)

### 3.1 Backend HPA

```yaml
# backend-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3.2 Orchestrator HPA

```yaml
# orchestrator-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrator
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
```

---

## 4. Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: alice-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - alicechatbot.com
    - api.alicechatbot.com
    secretName: alice-tls
  rules:
  - host: alicechatbot.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
  - host: api.alicechatbot.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

---

## 5. Service Mesh (Optional - Istio)

For advanced traffic management, observability, and security:

```yaml
# virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-vs
spec:
  hosts:
  - backend
  http:
  - route:
    - destination:
        host: backend
        port:
          number: 8000
    retries:
      attempts: 3
      perTryTimeout: 2s
    timeout: 10s
```

---

## 6. Scaling Strategy by Service

### 6.1 Stateless Services (Easy to Scale)

| Service | Strategy | Notes |
|---------|----------|-------|
| Backend | HPA (CPU/Memory) | Stateless, easy horizontal scaling |
| Orchestrator | HPA (CPU/Memory) | Stateless, uses external Redis for session |
| Frontend | HPA (CPU) | Static assets, highly cacheable |
| Dataflow | HPA (Kafka lag) | Scale based on Kafka consumer lag |

### 6.2 Stateful Services (Careful Scaling)

| Service | Strategy | Notes |
|---------|----------|-------|
| MongoDB | StatefulSet + Replica Set | Use MongoDB Operator for automation |
| Redis | Redis Sentinel/Cluster | Use Redis Operator for HA |
| Kafka | StatefulSet + KRaft | Native clustering, partition-based scaling |
| Weaviate | StatefulSet | Multi-node cluster for HA |

---

## 7. Network Topology

```
                    ┌─────────────────────────────────────┐
                    │           Ingress Controller         │
                    │         (nginx / traefik)            │
                    └─────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
              ┌─────▼─────┐                       ┌─────▼─────┐
              │  Frontend │                       │  Backend  │
              │  Service  │                       │  Service  │
              │  :3000    │                       │  :8000    │
              └───────────┘                       └─────┬─────┘
                                                        │
                    ┌───────────────────────────────────┤
                    │                                   │
              ┌─────▼─────┐                       ┌─────▼─────┐
              │   Kafka   │                       │   Redis   │
              │  Service  │                       │  Service  │
              │  :9092    │                       │  :6379    │
              └─────┬─────┘                       └───────────┘
                    │
              ┌─────▼─────┐
              │Orchestrator│
              │  Service   │
              │  :8001     │
              └─────┬─────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
  ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
  │  MongoDB  │ │ Redis │ │ Weaviate  │
  │  Service  │ │Service│ │  Service  │
  │  :27017   │ │:6379  │ │  :8080    │
  └───────────┘ └───────┘ └───────────┘
```

---

## 8. Deployment Commands

### 8.1 Initial Deployment

```bash
# Create namespace
kubectl create namespace alice

# Apply ConfigMaps and Secrets
kubectl apply -f k8s/configmaps/ -n alice
kubectl apply -f k8s/secrets/ -n alice

# Deploy stateful services first
kubectl apply -f k8s/mongodb/ -n alice
kubectl apply -f k8s/redis/ -n alice
kubectl apply -f k8s/kafka/ -n alice
kubectl apply -f k8s/weaviate/ -n alice

# Wait for stateful services to be ready
kubectl wait --for=condition=ready pod -l app=alice-mongodb -n alice --timeout=300s
kubectl wait --for=condition=ready pod -l app=alice-redis -n alice --timeout=300s
kubectl wait --for=condition=ready pod -l app=alice-kafka -n alice --timeout=300s

# Deploy application services
kubectl apply -f k8s/orchestrator/ -n alice
kubectl apply -f k8s/dataflow/ -n alice
kubectl apply -f k8s/backend/ -n alice
kubectl apply -f k8s/frontend/ -n alice

# Apply HPAs
kubectl apply -f k8s/hpa/ -n alice

# Apply Ingress
kubectl apply -f k8s/ingress/ -n alice
```

### 8.2 Manual Scaling

```bash
# Scale backend to 5 replicas
kubectl scale deployment backend --replicas=5 -n alice

# Scale orchestrator to 4 replicas
kubectl scale deployment orchestrator --replicas=4 -n alice

# Check scaling status
kubectl get hpa -n alice
kubectl get pods -n alice -o wide
```

### 8.3 Rolling Update

```bash
# Update backend image
kubectl set image deployment/backend backend=alice/backend:v2.0.0 -n alice

# Watch rollout status
kubectl rollout status deployment/backend -n alice

# Rollback if needed
kubectl rollout undo deployment/backend -n alice
```

---

## 9. Monitoring & Observability

### 9.1 Prometheus Metrics

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: alice-services
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      monitoring: enabled
  endpoints:
  - port: metrics
    interval: 15s
```

### 9.2 Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| CPU Utilization | < 70% | > 85% for 5min |
| Memory Utilization | < 80% | > 90% for 5min |
| Request Latency (p99) | < 500ms | > 1000ms for 5min |
| Error Rate | < 1% | > 5% for 2min |
| Kafka Consumer Lag | < 1000 | > 10000 for 10min |
| Pod Restart Count | 0 | > 3 per hour |

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

- **MongoDB**: Daily automated backups using mongodump
- **Redis**: RDB snapshots every 15 minutes
- **Weaviate**: Scheduled backups to S3/GCS
- **Kafka**: Log retention + topic mirroring

### 10.2 Multi-Region Setup (Future)

```
┌─────────────────┐     ┌─────────────────┐
│   Region A      │     │   Region B      │
│   (Primary)     │────▶│   (Standby)     │
│                 │     │                 │
│ ┌─────────────┐ │     │ ┌─────────────┐ │
│ │ K8s Cluster │ │     │ │ K8s Cluster │ │
│ └─────────────┘ │     │ └─────────────┘ │
└─────────────────┘     └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              Global Load Balancer
```

---

## 11. Cost Optimization

### 11.1 Resource Right-Sizing

- Start with minimal resources, scale based on actual usage
- Use Vertical Pod Autoscaler (VPA) for resource recommendations
- Reserved instances for baseline capacity

### 11.2 Spot/Preemptible Instances

```yaml
# Node pool for non-critical workloads
spec:
  nodeSelector:
    cloud.google.com/gke-spot: "true"
  tolerations:
  - key: "cloud.google.com/gke-spot"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

---

## 12. Implementation Roadmap

| Phase | Tasks | Timeline |
|-------|-------|----------|
| Phase 1 | Containerize all services, create K8s manifests | Week 1-2 |
| Phase 2 | Deploy to staging cluster, validate functionality | Week 3 |
| Phase 3 | Set up monitoring, alerting, and HPA | Week 4 |
| Phase 4 | Production deployment with canary release | Week 5 |
| Phase 5 | Performance testing and optimization | Week 6 |
| Phase 6 | Documentation and runbook creation | Week 7 |

---

## 13. Appendix

### 13.1 Folder Structure

```
k8s/
├── namespace.yaml
├── configmaps/
│   ├── backend-config.yaml
│   ├── orchestrator-config.yaml
│   └── frontend-config.yaml
├── secrets/
│   ├── mongodb-secrets.yaml
│   └── app-secrets.yaml
├── mongodb/
│   ├── statefulset.yaml
│   ├── service.yaml
│   └── pvc.yaml
├── redis/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── pvc.yaml
├── kafka/
│   ├── statefulset.yaml
│   └── service.yaml
├── weaviate/
│   ├── statefulset.yaml
│   └── service.yaml
├── orchestrator/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
├── dataflow/
│   ├── deployment.yaml
│   └── service.yaml
├── backend/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
├── frontend/
│   ├── deployment.yaml
│   └── service.yaml
├── ingress/
│   └── ingress.yaml
└── hpa/
    ├── backend-hpa.yaml
    └── orchestrator-hpa.yaml
```

### 13.2 Environment Variables

All sensitive data should be stored in Kubernetes Secrets and referenced via `envFrom` or `valueFrom.secretKeyRef`.

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Author**: Alice Chatbot Team
