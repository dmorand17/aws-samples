# AWS ParallelCluster with Open OnDemand Integration

This repository contains scripts and configuration files for setting up and managing AWS ParallelCluster with Open OnDemand (OOD) integration. The tools provided help automate the configuration process and ensure proper setup of authentication mechanisms.

## Overview

The repository includes scripts for:

- Generating ParallelCluster configuration files based on your OOD stack
- Creating Munge authentication keys for Slurm
- Setting up proper integration between ParallelCluster and Open OnDemand

## Prerequisites

- AWS CLI installed and configured
- Python 3.x
- An existing Open OnDemand stack deployed in your AWS account
- Appropriate AWS credentials with necessary permissions

## Scripts

### create_pcluster_config.sh

A bash script that generates a ParallelCluster configuration file by reading outputs from your existing OOD stack.

#### Features

- Automatic configuration of head node, compute nodes, and login nodes
- Integration with your OOD environment
- Configuration of Slurm queues for both general workloads and interactive desktop sessions
- Security group and IAM policy configuration

#### Usage

```bash
./create_pcluster_config.sh <STACK_NAME> [REGION] [DOMAIN_1] [DOMAIN_2]
```

Parameters:

- `STACK_NAME` (required): Your OOD CloudFormation stack name
- `REGION` (optional): AWS region (default: us-east-1)
- `DOMAIN_1` (optional): First part of domain name (default: hpclab)
- `DOMAIN_2` (optional): Second part of domain name (default: local)

Example:

```bash
./create_pcluster_config.sh my-ood-stack us-west-2 mylab example
```

### create_munge_key.py

A Python script that generates a secure Munge key for Slurm authentication between cluster nodes.

#### Features

- Generates a 128-byte random key
- Outputs base64-encoded key suitable for Slurm configuration
- Can be used with AWS Secrets Manager for secure key storage

#### Usage

```bash
python scripts/create_munge_key.py
```

Example with AWS Secrets Manager:

```bash
# Generate and store key in AWS Secrets Manager
python scripts/create_munge_key.py | aws secretsmanager create-secret \
    --name my-munge-key \
    --secret-string file:///dev/stdin
```

## Deployment Workflow

1. **Prepare Environment**

   - Ensure AWS CLI is configured
   - Verify Python 3.x is installed
   - Deploy Open OnDemand stack if not already done

2. **Generate Munge Key**

   ```bash
   python scripts/create_munge_key.py > munge_key.txt
   ```

3. **Store Munge Key in AWS Secrets Manager**

   ```bash
   aws secretsmanager create-secret --name my-munge-key --secret-string file://munge_key.txt
   ```

4. **Generate ParallelCluster Configuration**

   ```bash
   ./create_pcluster_config.sh my-ood-stack
   ```

5. **Create ParallelCluster**
   ```bash
   pcluster create-cluster --cluster-name my-cluster --cluster-configuration pcluster-config.yml
   ```

## Security Considerations

- Always store sensitive information (like Munge keys) in AWS Secrets Manager
- Review and adjust security group configurations as needed
- Follow the principle of least privilege when configuring IAM roles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
