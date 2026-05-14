# 카카오맵 API
resource "aws_secretsmanager_secret" "kakao_map" {
  name        = "homelens/${var.env}/kakao/map-api"
  description = "카카오맵 REST API Key, JavaScript API Key"

  tags = { Env = var.env }
}

# 네이버 뉴스 API
resource "aws_secretsmanager_secret" "naver_news" {
  name        = "homelens/${var.env}/naver/news-api"
  description = "네이버 뉴스 API Client ID / Secret"

  tags = { Env = var.env }
}

# 국토부 실거래가 API
resource "aws_secretsmanager_secret" "molit" {
  name        = "homelens/${var.env}/molit/real-estate-api"
  description = "국토부 공공데이터 API Key"

  tags = { Env = var.env }
}

# RDS 접속 정보
resource "aws_secretsmanager_secret" "rds" {
  name        = "homelens/${var.env}/rds/postgres"
  description = "username, password, host, port, dbname"

  tags = { Env = var.env }
}

# Redis auth token
resource "aws_secretsmanager_secret" "redis" {
  name        = "homelens/${var.env}/redis/auth"
  description = "Redis auth token (prod 필수)"

  tags = { Env = var.env }
}

# Bedrock 설정
resource "aws_secretsmanager_secret" "bedrock" {
  name        = "homelens/${var.env}/bedrock/config"
  description = "Bedrock 모델 ID, 리전 등 설정값"

  tags = { Env = var.env }
}