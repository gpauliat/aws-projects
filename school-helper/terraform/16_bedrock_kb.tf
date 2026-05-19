# Bedrock Knowledge Base with OpenSearch Serverless Vector Store

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# IAM Role for Bedrock Knowledge Base
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "kb_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "kb" {
  name               = "${var.project_name}-kb-role"
  assume_role_policy = data.aws_iam_policy_document.kb_assume_role.json
}

data "aws_iam_policy_document" "kb" {
  # S3 — read PDFs from the storage bucket
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.pdf_storage.arn,
      "${aws_s3_bucket.pdf_storage.arn}/*",
    ]
  }

  # OpenSearch Serverless — write and read vectors
  statement {
    effect    = "Allow"
    actions   = ["aoss:APIAccessAll"]
    resources = [aws_opensearchserverless_collection.kb.arn]
  }

  # Bedrock — invoke the embedding model
  statement {
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"]
  }
}

resource "aws_iam_role_policy" "kb" {
  name   = "${var.project_name}-kb-policy"
  role   = aws_iam_role.kb.id
  policy = data.aws_iam_policy_document.kb.json
}

# ---------------------------------------------------------------------------
# OpenSearch Serverless Collection (Vector Store)
# ---------------------------------------------------------------------------

resource "aws_opensearchserverless_security_policy" "kb_encryption" {
  name = "${var.project_name}-kb-enc"
  type = "encryption"
  policy = jsonencode({
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${var.project_name}-kb"]
    }]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "kb_network" {
  name = "${var.project_name}-kb-net"
  type = "network"
  policy = jsonencode([{
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${var.project_name}-kb"]
    }]
    AllowFromPublic = true
  }])
}

resource "aws_opensearchserverless_access_policy" "kb" {
  name = "${var.project_name}-kb-access"
  type = "data"
  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/${var.project_name}-kb/*"]
        Permission   = ["aoss:CreateIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.project_name}-kb"]
        Permission   = ["aoss:CreateCollectionItems", "aoss:DescribeCollectionItems", "aoss:UpdateCollectionItems"]
      },
    ]
    Principal = [aws_iam_role.kb.arn, data.aws_caller_identity.current.arn]
  }])
}

resource "aws_opensearchserverless_collection" "kb" {
  name = "${var.project_name}-kb"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.kb_encryption,
    aws_opensearchserverless_security_policy.kb_network,
    aws_opensearchserverless_access_policy.kb,
  ]

  tags = {
    Name = "${var.project_name}-kb"
  }
}

# ---------------------------------------------------------------------------
# Bedrock Knowledge Base
# ---------------------------------------------------------------------------

# Create the vector index in OpenSearch Serverless before the KB references it
resource "null_resource" "kb_index" {
  depends_on = [aws_opensearchserverless_collection.kb]

  provisioner "local-exec" {
    interpreter = ["python", "-c"]
    command     = <<-EOT
import subprocess, sys, json

body = json.dumps({
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {
                    "engine": "faiss",
                    "space_type": "l2",
                    "name": "hnsw",
                    "parameters": {}
                }
            },
            "AMAZON_BEDROCK_TEXT_CHUNK": {
                "type": "text"
            },
            "AMAZON_BEDROCK_METADATA": {
                "type": "text",
                "index": False
            }
        }
    }
})

endpoint = "${aws_opensearchserverless_collection.kb.collection_endpoint}/bedrock-knowledge-base-default-index"
result = subprocess.run(
    ["awscurl", "--service", "aoss", "--region", "${var.aws_region}", "-X", "PUT", endpoint, "-H", "Content-Type: application/json", "-d", body],
    capture_output=True, text=True
)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
    EOT
  }
}

resource "aws_bedrockagent_knowledge_base" "this" {
  name     = "${var.project_name}-kb"
  role_arn = aws_iam_role.kb.arn

  depends_on = [null_resource.kb_index]

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.kb.arn
      vector_index_name = "bedrock-knowledge-base-default-index"
      field_mapping {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }

  tags = {
    Name = "${var.project_name}-kb"
  }
}

# ---------------------------------------------------------------------------
# Bedrock Data Source (S3 PDFs)
# ---------------------------------------------------------------------------

resource "aws_bedrockagent_data_source" "pdfs" {
  name                 = "${var.project_name}-pdf-source"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.this.id
  data_deletion_policy = "RETAIN"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = aws_s3_bucket.pdf_storage.arn
      inclusion_prefixes = ["pdfs/"]
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration {
        max_tokens         = 300
        overlap_percentage = 20
      }
    }
  }
}
