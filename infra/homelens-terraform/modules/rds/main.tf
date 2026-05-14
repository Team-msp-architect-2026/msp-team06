resource "aws_db_subnet_group" "main" {
    name     = "${var.project_name}-${var.env}-rds"
    subnet_ids = var.db_subnet_ids

    tags = { Name = "${var.project_name}-${var.env}-rds-subnet-group" }

}

resource "aws_db_parameter_group" "main" {
    name = "${var.project_name}-${var.env}-pg17"
    family = "postgres17"

    parameter {
        name = "shared_preload_libraries"
        value = "postgis-3"
    
    }
}

resource "aws_db_instance" "main" {
    identifier = "${var.project_name}-${var.env}-postgres"

    engine         = "postgres"
    engine_version = "17"

    instance_class        = var.instance_class
    multi_az              = var.multi_az
    storage_type          = "gp3"
    allocated_storage     = var.allocated_storage
    max_allocated_storage = var.max_allocated_storage

    db_name = "homelens"
    username = "homelens_admin"
    manage_master_user_password = true

    db_subnet_group_name  = aws_db_subnet_group.main.name
    parameter_group_name  = aws_db_parameter_group.main.name
    vpc_security_group_ids = [var.rds_sg_id]

    backup_retention_period = var.env == "prod" ? 7 : 1
    deletion_protection     = var.env == "prod" ? true : false
    skip_final_snapshot     = var.env == "prod" ? false : true

    tags = { Env = var.env }
}
