variable "project_name" {
    type  = string
    default = "homelens"
}

variable "env" {
    type      = string
    description = "dev | staging | prod"
}

variable "db_subnet_ids" {
    type      = list(string)
    description = "networking 모듈에서 받음"
}

variable "redis_sg_id" {
    type      = string
    description = "networking 모듈에서 받음"
}

variable "node_type" {
    type      = string
    description = "dev=cache.t4g.micro / staging=cache.t4g.small / prod=cache.t4g.small"
}

variable "redis_auth_token" {
    type       = string
    default    = null
    sensitive  = true
    description = "prod 필수 / dev,staging null"
}