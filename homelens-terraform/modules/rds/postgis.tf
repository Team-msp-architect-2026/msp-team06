# PostGIS 3.5 설치는 DB 프로비저닝 후 초기화 스크립트에서 수행한다.
# Terraform은 RDS 인스턴스 생성 및 파라미터 그룹까지만 담당하며,
# CREATE EXTENSION postgis 실행은 별도 마이그레이션(예: Flyway/Alembic)에 위임한다.
#
# 아래 null_resource는 첫 apply 시 확장 설치 여부를 문서화 목적으로만 유지한다.
# 실제 환경에서는 마이그레이션 파이프라인의 V001__enable_postgis.sql 로 대체한다.

locals {
  postgis_note = "PostGIS 3.5 extension must be enabled via migration: CREATE EXTENSION IF NOT EXISTS postgis;"
}

output "postgis_install_note" {
  description = "PostGIS installation reminder"
  value       = local.postgis_note
}
