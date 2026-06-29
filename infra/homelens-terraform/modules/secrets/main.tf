# 카카오맵 API
resource "aws_secretsmanager_secret" "kakao_map" {
  name                    = "homelens/${var.env}/kakao/map-api"
  description             = "카카오맵 REST API Key, JavaScript API Key"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "kakao_map" {
  secret_id = aws_secretsmanager_secret.kakao_map.id
  secret_string = jsonencode({
    rest_api_key = var.kakao_rest_api_key
    js_api_key   = var.kakao_js_api_key
  })
}

# 네이버 뉴스 API
resource "aws_secretsmanager_secret" "naver_news" {
  name                    = "homelens/${var.env}/naver/news-api"
  description             = "네이버 뉴스 API Client ID / Secret"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "naver_news" {
  secret_id = aws_secretsmanager_secret.naver_news.id
  secret_string = jsonencode({
    client_id     = var.naver_client_id
    client_secret = var.naver_client_secret
  })
}

# 국토부 실거래가 API
resource "aws_secretsmanager_secret" "molit" {
  name                    = "homelens/${var.env}/molit/real-estate-api"
  description             = "국토부 공공데이터 API Key"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "molit" {
  secret_id = aws_secretsmanager_secret.molit.id
  secret_string = jsonencode({
    service_key = var.molit_service_key
  })
}

# 행안부 도로명주소 API
resource "aws_secretsmanager_secret" "mois" {
  name                    = "homelens/${var.env}/mois/address-api"
  description             = "행안부 도로명주소 API 서비스키"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "mois" {
  secret_id = aws_secretsmanager_secret.mois.id
  secret_string = jsonencode({
    service_key = var.mois_service_key
  })
}

# RDS 접속 정보
# password는 RDS manage_master_user_password가 관리 — password_secret_arn으로 참조
resource "aws_secretsmanager_secret" "rds" {
  name                    = "homelens/${var.env}/rds/postgres"
  description             = "username, host, port, dbname + RDS 관리형 password ARN"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "rds" {
  secret_id = aws_secretsmanager_secret.rds.id
  secret_string = jsonencode({
    host               = split(":", var.rds_endpoint)[0]
    port               = 5432
    dbname             = "homelens"
    username           = "homelens_admin"
    password_secret_arn = var.rds_secret_arn
  })
}

# terraform apply 시 리소스 정책이 초기화되므로 코드로 관리
resource "aws_secretsmanager_secret_policy" "rds" {
  secret_arn = aws_secretsmanager_secret.rds.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::611058323802:user/student12" }
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
      }
    ]
  })
}

# AWS 관리형 시크릿(rds!db-...)에도 student12 읽기 권한
resource "aws_secretsmanager_secret_policy" "rds_managed" {
  secret_arn = var.rds_secret_arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::611058323802:user/student12" }
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
      }
    ]
  })
}

# Redis 접속 정보 (dev는 auth_token 없음)
resource "aws_secretsmanager_secret" "redis" {
  name                    = "homelens/${var.env}/redis/auth"
  description             = "Redis 접속 정보 (prod는 auth_token 추가 필요)"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host       = var.redis_endpoint
    port       = 6379
    auth_token = var.redis_auth_token != null ? var.redis_auth_token : ""
  })
}

# Bedrock 설정
resource "aws_secretsmanager_secret" "bedrock" {
  name                    = "homelens/${var.env}/bedrock/config"
  description             = "Bedrock 모델 ID, 리전 등 설정값"
  recovery_window_in_days = 0

  tags = { Env = var.env }
}

resource "aws_secretsmanager_secret_version" "bedrock" {
  secret_id = aws_secretsmanager_secret.bedrock.id
  secret_string = jsonencode({
    model_id = var.bedrock_model_id
    region   = var.bedrock_region
  })
}