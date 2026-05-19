# Quiz Generator

Application web qui permet d'uploader des documents PDF et de générer automatiquement des quiz à choix multiples à partir de leur contenu grâce à l'IA (Amazon Bedrock). Les utilisateurs peuvent ensuite passer les quiz, suivre leurs scores et visualiser leur progression.

## Architecture

```
.
├── frontend/                    # SPA React (TypeScript + Vite)
│   ├── src/
│   │   ├── components/          # Composants réutilisables (PdfUploader, QuizResults, QuizHistory)
│   │   ├── pages/               # Pages (Dashboard, Quiz, History, Login, Register, ResetPassword)
│   │   ├── services/            # Client API (api.ts) et wrapper auth (auth.ts)
│   │   └── types/               # Interfaces TypeScript partagées
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── terraform/                   # Infrastructure as Code
│   ├── 01_variables.tf          # Variables d'entrée
│   ├── 02_providers.tf          # Configuration provider AWS + tags par défaut
│   ├── 03_cognito.tf            # User pool et client
│   ├── 04_dynamodb.tf           # Tables : pdfs, quizzes, quiz-attempts
│   ├── 05_s3.tf                 # Buckets S3 (stockage PDF + hébergement frontend)
│   ├── 06_lambda_common.tf      # Rôles IAM partagés, policies, log groups
│   ├── 07_lambda_pdf_upload.tf  # Lambda upload PDF (URL présignée)
│   ├── 08_lambda_kb_sync.tf     # Lambda sync Knowledge Base
│   ├── 09_lambda_quiz_generation.tf  # Lambda génération de quiz via Bedrock
│   ├── 10_lambda_quiz_taking.tf # Lambda passage de quiz
│   ├── 11_lambda_history.tf     # Lambda historique et progression
│   ├── 12_lambda_management.tf  # Lambda gestion (listing, suppression cascade)
│   ├── 13_api_gateway.tf        # REST API, routes, CORS, intégrations
│   ├── 14_cloudfront.tf         # Distribution CDN
│   ├── 15_outputs.tf            # Outputs Terraform
│   ├── 16_bedrock_kb.tf         # Knowledge Base + OpenSearch Serverless
│   ├── 17_waf.tf                # WAF restriction IP
│   ├── terraform.tfvars         # Valeurs des variables (ne pas commiter publiquement)
│   └── lambdas/                 # Code source des Lambda functions
│       ├── pdf_upload/          # Génération d'URL présignée + enregistrement DynamoDB
│       ├── kb_sync/             # Déclenchement ingestion Bedrock Knowledge Base
│       ├── quiz_generation/     # Génération de quiz IA via Bedrock (RAG)
│       ├── quiz_taking/         # Récupération de quiz et soumission de réponses
│       ├── history/             # Historique des tentatives et suivi de progression
│       └── management/          # Listing PDF/quiz et suppression en cascade
```

## Stack technique

| Couche      | Technologies                                                                 |
| ----------- | ---------------------------------------------------------------------------- |
| Frontend    | React 18, TypeScript (strict), Vite 6, react-router-dom v6, aws-amplify v6  |
| Backend     | Python 3.x, AWS Lambda, API Gateway REST, DynamoDB, boto3                    |
| IA          | Amazon Bedrock (modèles fondation), Titan Embed v2, RAG via Knowledge Base   |
| Auth        | Cognito (email/password, JWT)                                                |
| Stockage    | S3 (PDF + frontend statique), OpenSearch Serverless (vecteurs)               |
| Hébergement | CloudFront + S3 (frontend), API Gateway (backend)                            |
| Sécurité    | WAF (restriction IP), Cognito Authorizer                                     |
| Infra       | Terraform (déploiement unifié)                             |

## Fonctionnalités

- **Upload PDF** : Upload de fichiers PDF vers S3 via URL présignée, ingestion dans une Knowledge Base Bedrock pour la recherche sémantique
- **Génération de quiz** : Génération automatique de questions à choix multiples à partir du contenu PDF via RAG (Retrieval-Augmented Generation)
- **Passage de quiz** : Réponse aux questions générées avec scoring immédiat et feedback correct/incorrect
- **Historique et progression** : Consultation des tentatives passées, suivi de la progression par PDF (scores moyens, nombre de tentatives)
- **Gestion des ressources** : Suppression de PDF et quiz avec suppression en cascade des données associées
- **Authentification** : Inscription avec vérification email, connexion, réinitialisation de mot de passe

## API REST

| Méthode  | Route                          | Description                          | Lambda            |
| -------- | ------------------------------ | ------------------------------------ | ----------------- |
| `POST`   | `/pdfs/upload-url`             | Obtenir une URL présignée d'upload   | pdf_upload        |
| `GET`    | `/pdfs`                        | Lister les PDF de l'utilisateur      | management        |
| `DELETE` | `/pdfs/{pdfId}`                | Supprimer un PDF (cascade)           | management        |
| `POST`   | `/pdfs/{pdfId}/generate-quiz`  | Générer un quiz à partir d'un PDF    | quiz_generation   |
| `GET`    | `/quizzes`                     | Lister les quiz de l'utilisateur     | quiz_taking       |
| `GET`    | `/quizzes/{quizId}`            | Récupérer un quiz                    | quiz_taking       |
| `POST`   | `/quizzes/{quizId}/submit`     | Soumettre les réponses d'un quiz     | quiz_taking       |
| `DELETE` | `/quizzes/{quizId}`            | Supprimer un quiz                    | management        |
| `GET`    | `/history`                     | Historique des tentatives            | history           |
| `GET`    | `/history/{attemptId}`         | Détail d'une tentative               | history           |
| `GET`    | `/progress/pdf/{pdfId}`        | Progression par PDF                  | history           |

Toutes les routes (sauf OPTIONS) sont protégées par un authorizer Cognito.

## Quick Start

### Prérequis

- AWS CLI configuré
- Terraform ≥ 1.0
- Python 3.x
- Node.js 18+

### Déploiement de l'infrastructure

```bash
cd terraform
terraform init
terraform apply
```

### Configuration du frontend

Créer un fichier `frontend/.env` avec les outputs Terraform :

```bash
cd terraform
terraform output api_gateway_url
terraform output cognito_user_pool_id
terraform output cognito_client_id
```

```env
VITE_API_BASE_URL=<api_gateway_url>
VITE_COGNITO_USER_POOL_ID=<cognito_user_pool_id>
VITE_COGNITO_CLIENT_ID=<cognito_client_id>
```

### Lancement en développement

```bash
cd frontend
npm install
npm run dev        # Serveur de dev sur le port 3000
```

### Build de production

```bash
cd frontend
npm run build      # Compilation TypeScript + build Vite
npm run preview    # Prévisualisation du build
```

### Accès à l'application

```bash
cd terraform
terraform output cloudfront_domain_name
```

## Développement

### Frontend

```bash
cd frontend
npm install
npm run dev        # Serveur de dev (port 3000)
npm run build      # Build production (tsc + vite build)
npm run preview    # Prévisualisation du build
```

### Infrastructure

```bash
cd terraform
terraform init     # Initialiser les providers
terraform plan     # Prévisualiser les changements
terraform apply    # Appliquer les changements
terraform destroy  # Détruire toutes les ressources
```

### Déploiement ciblé

```bash
# Une Lambda spécifique
terraform apply -target='aws_lambda_function.quiz_generation'

# Frontend uniquement
terraform apply -target='aws_s3_bucket.frontend'
```

## Sécurité

- S3 privé, accès via CloudFront OAC uniquement
- HTTPS sur tous les endpoints
- Authentification JWT via Cognito
- WAF avec restriction d'accès par IP
- DynamoDB chiffré au repos
- Toutes les routes API protégées par un authorizer Cognito
- Ne jamais commiter `.env` ou `terraform.tfvars` dans un dépôt public

## Variables d'environnement

### Frontend (via `.env`)

| Variable                    | Description                    |
| --------------------------- | ------------------------------ |
| `VITE_API_BASE_URL`        | URL de l'API Gateway           |
| `VITE_COGNITO_USER_POOL_ID`| ID du User Pool Cognito        |
| `VITE_COGNITO_CLIENT_ID`   | ID du client Cognito           |

### Lambda (configurées via Terraform)

| Variable              | Description                              |
| --------------------- | ---------------------------------------- |
| `S3_BUCKET_NAME`      | Bucket S3 de stockage des PDF            |
| `DYNAMODB_TABLE_NAME` | Table DynamoDB principale                |
| `MAX_FILE_SIZE`       | Taille maximale des fichiers uploadés    |
| `KNOWLEDGE_BASE_ID`   | ID de la Knowledge Base Bedrock          |
| `DATA_SOURCE_ID`      | ID de la data source Bedrock             |
