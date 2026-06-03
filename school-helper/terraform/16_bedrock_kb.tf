# Bedrock Knowledge Base with S3 Vectors Store

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# S3 Vector Bucket and Index
# ---------------------------------------------------------------------------

resource "aws_s3vectors_vector_bucket" "kb" {
  vector_bucket_name = "${var.project_name}-kb-vectors"
}

resource "aws_s3vectors_index" "kb" {
  index_name         = "bedrock-knowledge-base-default-index"
  vector_bucket_name = aws_s3vectors_vector_bucket.kb.vector_bucket_name
  dimension          = 1024
  distance_metric    = "cosine"
  data_type          = "float32"
}

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

  # S3 Vectors — read and write vectors
  statement {
    effect = "Allow"
    actions = [
      "s3vectors:CreateIndex",
      "s3vectors:DeleteIndex",
      "s3vectors:GetIndex",
      "s3vectors:ListIndexes",
      "s3vectors:PutVectors",
      "s3vectors:GetVectors",
      "s3vectors:DeleteVectors",
      "s3vectors:QueryVectors",
      "s3vectors:ListVectors",
    ]
    resources = [
      aws_s3vectors_vector_bucket.kb.vector_bucket_arn,
      "${aws_s3vectors_vector_bucket.kb.vector_bucket_arn}/*",
    ]
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
# Bedrock Knowledge Base
# ---------------------------------------------------------------------------

resource "aws_bedrockagent_knowledge_base" "this" {
  name     = "gautier-quiz-kb"
  role_arn = aws_iam_role.kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }

  storage_configuration {
    type = "S3_VECTORS"
    s3_vectors_configuration {
      vector_bucket_arn = aws_s3vectors_vector_bucket.kb.vector_bucket_arn
      index_name        = aws_s3vectors_index.kb.index_name
    }
  }

  lifecycle {
    create_before_destroy = false
  }

  tags = {
    Name = "gautier-quiz-kb"
  }
}

# ---------------------------------------------------------------------------
# Bedrock Data Source (S3 PDFs)
# ---------------------------------------------------------------------------

resource "aws_bedrockagent_data_source" "pdfs" {
  name                 = "${var.project_name}-pdf-source"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.this.id
  data_deletion_policy = "DELETE"

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
