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
## 📁 Estructura del Proyecto
```
MediSupply-Backend/
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       ├── outputs.tf
│       └── modules/
│           ├── networking/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── database/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── orders/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           ├── bff-venta/
│           │   ├── main.tf
│           │   ├── variables.tf
│           │   └── outputs.tf
│           └── consumer/
│               ├── main.tf
│               ├── variables.tf
│               └── outputs.tf
├── orders-service/
├── bff-venta/
├── consumer-lb/
├── catalogo-service/
├── cliente-service/
├── ruta-service/
└── README.md
```
\```

---

## 🏗️ Estructura de Infraestructura (Terraform)
```
infra/terraform/
│
├── 📄 Archivos Principales
│   ├── main.tf                 # Backend S3, Provider, VPC, RDS, Llamadas a módulos
│   ├── variables.tf            # Variables globales del proyecto
│   ├── terraform.tfvars        # Valores de configuración
│   └── outputs.tf              # Outputs agregados
│
└── 📦 modules/                 # Módulos por servicio
    │
    ├── networking/             # [Platform Team]
    │   ├── main.tf            # VPC, Subnets, NAT Gateway, ECS Cluster
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── database/               # [Platform Team]
    │   ├── main.tf            # RDS PostgreSQL, Secrets Manager
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── orders/                 # [Backend Team]
    │   ├── main.tf            # ECS Task Definition, Service, IAM
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── bff-venta/              # [Frontend Team]
    │   ├── main.tf            # ALB, ECS Service, SQS Producer
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── consumer/               # [Backend Team]
        ├── main.tf            # SQS Queues, HAProxy, Worker
        ├── variables.tf
        └── outputs.tf