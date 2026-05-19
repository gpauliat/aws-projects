# API Gateway REST API

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api"
  description = "Quiz Generator REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-api"
  }
}

# ---------------------------------------------------------------------------
# Cognito Authorizer
# ---------------------------------------------------------------------------

resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${var.project_name}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.main.arn]
  identity_source = "method.request.header.Authorization"
}

# ---------------------------------------------------------------------------
# API Resources (URL paths)
# ---------------------------------------------------------------------------

# /pdfs
resource "aws_api_gateway_resource" "pdfs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "pdfs"
}

# /pdfs/upload-url
resource "aws_api_gateway_resource" "pdfs_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.pdfs.id
  path_part   = "upload-url"
}

# /pdfs/{pdfId}
resource "aws_api_gateway_resource" "pdfs_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.pdfs.id
  path_part   = "{pdfId}"
}

# /pdfs/{pdfId}/generate-quiz
resource "aws_api_gateway_resource" "pdfs_pdfid_generate_quiz" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.pdfs_pdfid.id
  path_part   = "generate-quiz"
}

# /quizzes
resource "aws_api_gateway_resource" "quizzes" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "quizzes"
}

# /quizzes/{quizId}
resource "aws_api_gateway_resource" "quizzes_quizid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.quizzes.id
  path_part   = "{quizId}"
}

# /quizzes/{quizId}/submit
resource "aws_api_gateway_resource" "quizzes_quizid_submit" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.quizzes_quizid.id
  path_part   = "submit"
}

# /history
resource "aws_api_gateway_resource" "history" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "history"
}

# /history/{attemptId}
resource "aws_api_gateway_resource" "history_attemptid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.history.id
  path_part   = "{attemptId}"
}

# /progress
resource "aws_api_gateway_resource" "progress" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "progress"
}

# /progress/pdf
resource "aws_api_gateway_resource" "progress_pdf" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.progress.id
  path_part   = "pdf"
}

# /progress/pdf/{pdfId}
resource "aws_api_gateway_resource" "progress_pdf_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.progress_pdf.id
  path_part   = "{pdfId}"
}

# ---------------------------------------------------------------------------
# Methods and Integrations — POST /pdfs/upload-url → PDF Upload Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "post_pdfs_upload_url" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_upload_url.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "post_pdfs_upload_url" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.pdfs_upload_url.id
  http_method             = aws_api_gateway_method.post_pdfs_upload_url.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.pdf_upload.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /pdfs → Management Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_pdfs" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_pdfs" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.pdfs.id
  http_method             = aws_api_gateway_method.get_pdfs.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.management.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — DELETE /pdfs/{pdfId} → Management Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "delete_pdfs_pdfid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_pdfid.id
  http_method   = "DELETE"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "delete_pdfs_pdfid" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.pdfs_pdfid.id
  http_method             = aws_api_gateway_method.delete_pdfs_pdfid.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.management.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — POST /pdfs/{pdfId}/generate-quiz → Quiz Generation Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "post_pdfs_pdfid_generate_quiz" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "post_pdfs_pdfid_generate_quiz" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method             = aws_api_gateway_method.post_pdfs_pdfid_generate_quiz.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.quiz_generation.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /quizzes → Quiz Taking Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_quizzes" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_quizzes" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.quizzes.id
  http_method             = aws_api_gateway_method.get_quizzes.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.quiz_taking.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /quizzes/{quizId} → Quiz Taking Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_quizzes_quizid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes_quizid.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_quizzes_quizid" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.quizzes_quizid.id
  http_method             = aws_api_gateway_method.get_quizzes_quizid.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.quiz_taking.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — POST /quizzes/{quizId}/submit → Quiz Taking Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "post_quizzes_quizid_submit" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "post_quizzes_quizid_submit" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method             = aws_api_gateway_method.post_quizzes_quizid_submit.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.quiz_taking.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — DELETE /quizzes/{quizId} → Management Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "delete_quizzes_quizid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes_quizid.id
  http_method   = "DELETE"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "delete_quizzes_quizid" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.quizzes_quizid.id
  http_method             = aws_api_gateway_method.delete_quizzes_quizid.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.management.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /history → History Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_history" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.history.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_history" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.history.id
  http_method             = aws_api_gateway_method.get_history.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.history.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /history/{attemptId} → History Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_history_attemptid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.history_attemptid.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_history_attemptid" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.history_attemptid.id
  http_method             = aws_api_gateway_method.get_history_attemptid.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.history.invoke_arn
}

# ---------------------------------------------------------------------------
# Methods and Integrations — GET /progress/pdf/{pdfId} → History Lambda
# ---------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_progress_pdf_pdfid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "get_progress_pdf_pdfid" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method             = aws_api_gateway_method.get_progress_pdf_pdfid.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.history.invoke_arn
}

# ---------------------------------------------------------------------------
# CORS — OPTIONS methods with mock integration
# ---------------------------------------------------------------------------

# CORS for /pdfs
resource "aws_api_gateway_method" "options_pdfs" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_pdfs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs.id
  http_method = aws_api_gateway_method.options_pdfs.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_pdfs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs.id
  http_method = aws_api_gateway_method.options_pdfs.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_pdfs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs.id
  http_method = aws_api_gateway_method.options_pdfs.http_method
  status_code = aws_api_gateway_method_response.options_pdfs.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /pdfs/upload-url
resource "aws_api_gateway_method" "options_pdfs_upload_url" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_upload_url.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_pdfs_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_upload_url.id
  http_method = aws_api_gateway_method.options_pdfs_upload_url.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_pdfs_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_upload_url.id
  http_method = aws_api_gateway_method.options_pdfs_upload_url.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_pdfs_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_upload_url.id
  http_method = aws_api_gateway_method.options_pdfs_upload_url.http_method
  status_code = aws_api_gateway_method_response.options_pdfs_upload_url.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /pdfs/{pdfId}
resource "aws_api_gateway_method" "options_pdfs_pdfid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_pdfid.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_pdfs_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_pdfs_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_pdfs_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid.http_method
  status_code = aws_api_gateway_method_response.options_pdfs_pdfid.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /pdfs/{pdfId}/generate-quiz
resource "aws_api_gateway_method" "options_pdfs_pdfid_generate_quiz" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_pdfs_pdfid_generate_quiz" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid_generate_quiz.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_pdfs_pdfid_generate_quiz" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid_generate_quiz.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_pdfs_pdfid_generate_quiz" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.pdfs_pdfid_generate_quiz.id
  http_method = aws_api_gateway_method.options_pdfs_pdfid_generate_quiz.http_method
  status_code = aws_api_gateway_method_response.options_pdfs_pdfid_generate_quiz.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /quizzes
resource "aws_api_gateway_method" "options_quizzes" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_quizzes" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes.id
  http_method = aws_api_gateway_method.options_quizzes.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_quizzes" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes.id
  http_method = aws_api_gateway_method.options_quizzes.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_quizzes" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes.id
  http_method = aws_api_gateway_method.options_quizzes.http_method
  status_code = aws_api_gateway_method_response.options_quizzes.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /quizzes/{quizId}
resource "aws_api_gateway_method" "options_quizzes_quizid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes_quizid.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_quizzes_quizid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid.id
  http_method = aws_api_gateway_method.options_quizzes_quizid.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_quizzes_quizid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid.id
  http_method = aws_api_gateway_method.options_quizzes_quizid.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_quizzes_quizid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid.id
  http_method = aws_api_gateway_method.options_quizzes_quizid.http_method
  status_code = aws_api_gateway_method_response.options_quizzes_quizid.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /quizzes/{quizId}/submit
resource "aws_api_gateway_method" "options_quizzes_quizid_submit" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_quizzes_quizid_submit" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method = aws_api_gateway_method.options_quizzes_quizid_submit.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_quizzes_quizid_submit" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method = aws_api_gateway_method.options_quizzes_quizid_submit.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_quizzes_quizid_submit" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.quizzes_quizid_submit.id
  http_method = aws_api_gateway_method.options_quizzes_quizid_submit.http_method
  status_code = aws_api_gateway_method_response.options_quizzes_quizid_submit.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /history
resource "aws_api_gateway_method" "options_history" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.history.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_history" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history.id
  http_method = aws_api_gateway_method.options_history.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_history" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history.id
  http_method = aws_api_gateway_method.options_history.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_history" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history.id
  http_method = aws_api_gateway_method.options_history.http_method
  status_code = aws_api_gateway_method_response.options_history.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /history/{attemptId}
resource "aws_api_gateway_method" "options_history_attemptid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.history_attemptid.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_history_attemptid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history_attemptid.id
  http_method = aws_api_gateway_method.options_history_attemptid.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_history_attemptid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history_attemptid.id
  http_method = aws_api_gateway_method.options_history_attemptid.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_history_attemptid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.history_attemptid.id
  http_method = aws_api_gateway_method.options_history_attemptid.http_method
  status_code = aws_api_gateway_method_response.options_history_attemptid.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS for /progress/pdf/{pdfId}
resource "aws_api_gateway_method" "options_progress_pdf_pdfid" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_progress_pdf_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method = aws_api_gateway_method.options_progress_pdf_pdfid.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_progress_pdf_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method = aws_api_gateway_method.options_progress_pdf_pdfid.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_progress_pdf_pdfid" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.progress_pdf_pdfid.id
  http_method = aws_api_gateway_method.options_progress_pdf_pdfid.http_method
  status_code = aws_api_gateway_method_response.options_progress_pdf_pdfid.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# ---------------------------------------------------------------------------
# Lambda Permissions — Allow API Gateway to invoke each Lambda
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "apigw_pdf_upload" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pdf_upload.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_quiz_generation" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.quiz_generation.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_quiz_taking" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.quiz_taking.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_history" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.history.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_management" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.management.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# ---------------------------------------------------------------------------
# Deployment and Stage
# ---------------------------------------------------------------------------

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.main.body))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.post_pdfs_upload_url,
    aws_api_gateway_integration.get_pdfs,
    aws_api_gateway_integration.delete_pdfs_pdfid,
    aws_api_gateway_integration.post_pdfs_pdfid_generate_quiz,
    aws_api_gateway_integration.get_quizzes,
    aws_api_gateway_integration.get_quizzes_quizid,
    aws_api_gateway_integration.post_quizzes_quizid_submit,
    aws_api_gateway_integration.delete_quizzes_quizid,
    aws_api_gateway_integration.get_history,
    aws_api_gateway_integration.get_history_attemptid,
    aws_api_gateway_integration.get_progress_pdf_pdfid,
    aws_api_gateway_integration.options_pdfs,
    aws_api_gateway_integration.options_pdfs_upload_url,
    aws_api_gateway_integration.options_pdfs_pdfid,
    aws_api_gateway_integration.options_pdfs_pdfid_generate_quiz,
    aws_api_gateway_integration.options_quizzes,
    aws_api_gateway_integration.options_quizzes_quizid,
    aws_api_gateway_integration.options_quizzes_quizid_submit,
    aws_api_gateway_integration.options_history,
    aws_api_gateway_integration.options_history_attemptid,
    aws_api_gateway_integration.options_progress_pdf_pdfid,
  ]
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }
}
