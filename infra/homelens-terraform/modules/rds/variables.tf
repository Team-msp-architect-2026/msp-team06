variable "project_name" {
    type   = string
    default = "homelens"
}

variable "env" {
    type       = string
    description = "dev | staging | prod"
}

variable "db_subnet_ids" {
   type       = list(string)
   description = "networking 모듈에서 받음"
}

variable "rds_sg_id" {
    type      = string
    description = "networking 모듈에서 받음"
}

variable "instance_class" {
    type      = string
    description = "dev=db.t4g.small / staging.prod=db.t4g.medium"
}

variable "multi_az" {
    type       = bool
    default    = false
    description = "prod만 true"   
}

variable "allocated_storage" {
    type     = number
    description = "dev=20 / staging=50 / prod=100 (GB)"
}

variable "max_allocated_storage" {
    type       = number
    description = "dev=30 / staging=50 / prod=200 (GB)"
}
