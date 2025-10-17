# MediSupply-Backend

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <your-repo>
cd <project-folder>

# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

MediSupply-Backend/
├── .github/
│   └── workflows/
├── .venv/
├── bff-venta/
├── catalogo-service/
├── cliente-service/
├── consumer-lb/
├── infra/
│   └── terraform/
│       ├── modules/
│       │   ├── bff-venta/
│       │   │   ├── main.tf
│       │   │   ├── variables.tf
│       │   │   └── outputs.tf
│       │   ├── consumer/
│       │   │   ├── main.tf
│       │   │   ├── variables.tf
│       │   │   └── outputs.tf
│       │   ├── database/
│       │   │   ├── main.tf
│       │   │   ├── variables.tf
│       │   │   └── outputs.tf
│       │   ├── networking/
│       │   │   ├── main.tf
│       │   │   ├── variables.tf
│       │   │   └── outputs.tf
│       │   └── orders/
│       │       ├── main.tf
│       │       ├── variables.tf
│       │       └── outputs.tf
│       ├── main.tf                    # Backend, Provider, VPC, DB, Módulos
│       ├── variables.tf               # Variables globales
│       ├── terraform.tfvars          # Valores de variables
│       ├── outputs.tf                 # Outputs principales
│       └── terraform.lock.hcl
├── orders-service/
├── ruta-service/
├── docker-compose.dev.yml
├── docker-compose.yml
└── README.md
```

---

## 🏗️ **Estructura de Infraestructura (Terraform)**
```
infra/terraform/
│
├── 🔧 Configuración Principal
│   ├── main.tf                    # Backend S3, Provider AWS, VPC, RDS, Llamadas a módulos
│   ├── variables.tf               # Variables globales del proyecto
│   ├── terraform.tfvars          # Valores de configuración (project, env, region)
│   └── outputs.tf                 # Outputs agregados (URLs, endpoints, comandos útiles)
│
└── 📦 Módulos por Servicio
    │
    ├── modules/networking/        # [Shared] VPC + ECS Cluster
    │   ├── main.tf               # VPC module, ECS Cluster, Security Groups
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── modules/database/          # [Shared] PostgreSQL RDS
    │   ├── main.tf               # RDS instance, Subnet groups, Secrets Manager
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── modules/orders/            # [Backend Team] Orders Service
    │   ├── main.tf               # ECS Task Definition, ECS Service, IAM Roles
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── modules/bff-venta/         # [Frontend Team] BFF + ALB
    │   ├── main.tf               # ALB, Target Group, ECS Service, ECR, SQS Producer
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── modules/consumer/          # [Backend Team] SQS Consumer + HAProxy
        ├── main.tf               # SQS Queues (FIFO + DLQ), HAProxy, Worker
        ├── variables.tf
        └── outputs.tf
```

---

## 🎯 **Diagrama de Responsabilidades**
```
┌─────────────────────────────────────────────────────────────┐
│                     INFRAESTRUCTURA                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 main.tf (Root)                                          │
│  ├─ Backend S3 + DynamoDB Lock                             │
│  ├─ Provider AWS                                            │
│  ├─ VPC (10.20.0.0/16)                                     │
│  ├─ RDS PostgreSQL (orders DB)                             │
│  └─ Calls to Modules ─────────────┐                        │
│                                    │                        │
├────────────────────────────────────┼────────────────────────┤
│  📦 MÓDULOS                        │                        │
├────────────────────────────────────┴────────────────────────┤
│                                                             │
│  🌐 modules/networking/            [Platform Team]          │
│     └─ Recursos compartidos (VPC, Subnets, NAT, Cluster)  │
│                                                             │
│  🗄️ modules/database/              [Platform Team]          │
│     └─ RDS, Secrets Manager, Parameter Groups              │
│                                                             │
│  📦 modules/orders/                [Backend Team]           │
│     └─ ECS Service, Task Definition, Security Groups       │
│                                                             │
│  🌐 modules/bff-venta/             [Frontend Team]          │
│     └─ ALB, ECS Service, SQS Producer, ECR                 │
│                                                             │
│  ⚙️ modules/consumer/               [Backend Team]           │
│     └─ SQS Queues, HAProxy, Worker, ECR                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Flujo de Dependencias**
```
main.tf
   │
   ├─> module "vpc"
   │   └─> outputs: vpc_id, subnets
   │
   ├─> resource "aws_ecs_cluster"
   │   └─> outputs: cluster_arn
   │
   ├─> resource "aws_db_instance"
   │   └─> outputs: db_endpoint, secrets_arn
   │
   ├─> module "orders" ──────┬─> Necesita: vpc_id, subnets, cluster_arn, db_secret
   │                         │
   ├─> module "consumer" ────┼─> Necesita: vpc_id, subnets, cluster_arn
   │                         │   └─> Outputs: sqs_queue_url
   │                         │
   └─> module "bff_venta" ───┴─> Necesita: vpc_id, subnets, cluster_arn, sqs_queue_url
                                 └─> Outputs: alb_dns_name
```

---

## 🎨 **Arquitectura AWS (Visual)**
```
┌─────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                 │
│  Region: us-east-1                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🌐 VPC (10.20.0.0/16)                                              │
│  ├─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  📍 AZ: us-east-1a              📍 AZ: us-east-1b          │   │
│  │  ├─ Public Subnet (10.20.1/24)  ├─ Public Subnet (10.20.2/24) │   │
│  │  │  └─ NAT Gateway              │                          │   │
│  │  │                               │                          │   │
│  │  ├─ Private Subnet (10.20.11/24)├─ Private Subnet (10.20.12/24)│
│  │  │  ├─ Orders ECS               │  ├─ Orders ECS (replica) │   │
│  │  │  ├─ Consumer ECS              │  ├─ Consumer ECS         │   │
│  │  │  ├─ BFF ECS                   │  ├─ BFF ECS             │   │
│  │  │  └─ RDS PostgreSQL (primary)  │  └─ RDS (standby)       │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🌍 Internet                                                        │
│     │                                                               │
│     ├──> ALB (BFF) ──> BFF ECS ──> SQS FIFO ──> Consumer ──> Orders│
│     │                      │                                        │
│     │                      └──> Orders Service ──> RDS             │
│                                                                     │
│  📊 Shared Services                                                 │
│  ├─ ECR (Container Images)                                          │
│  ├─ Secrets Manager (DB Credentials)                               │
│  ├─ CloudWatch Logs                                                 │
│  └─ CloudWatch Alarms                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘