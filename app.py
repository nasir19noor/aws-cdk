#!/usr/bin/env python3
import os
from aws_cdk import (
    App,
    Stack,
    Environment,
    CfnOutput,
    aws_ec2 as ec2,
)
from constructs import Construct

class InfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Step 1: Create VPC
        vpc = ec2.Vpc(
            self, "MyVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,  # Use 2 Availability Zones
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                # Public subnet configuration
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                # Private subnet configuration
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Step 2: Get the first public subnet (CDK creates subnets automatically)
        public_subnet = vpc.public_subnets[0]
        
        # Step 3: Internet Gateway is automatically created by CDK when using PUBLIC subnet type
        # But if you want to reference it explicitly, you can access it via:
        # vpc.internet_gateway_id

        # Step 4: Route Tables are automatically created and configured by CDK
        # Public subnets get routes to IGW, private subnets get routes to NAT Gateway

        # Step 5: Create Security Group
        security_group = ec2.SecurityGroup(
            self, "MySecurityGroup",
            vpc=vpc,
            description="Security group for EC2 instance",
            allow_all_outbound=True
        )

        # Add inbound rules to security group
        # SSH access
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="SSH access"
        )

        # HTTP access
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP access"
        )

        # HTTPS access
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS access"
        )

        # Step 6: Create Key Pair (you'll need to create this manually or import existing one)
        # For this example, we'll assume you have a key pair named "my-key-pair"
        key_pair_name = "my-key-pair"  # Change this to your existing key pair name

        # Step 7: Create EC2 Instance
        # Get the latest Amazon Linux 2 AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux2(
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )

        # Create EC2 instance
        ec2_instance = ec2.Instance(
            self, "MyEC2Instance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.MICRO
            ),
            machine_image=amzn_linux,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=security_group,
            key_name=key_pair_name,
            user_data=ec2.UserData.for_linux()
        )

        # Add user data script to install and start Apache web server
        ec2_instance.user_data.add_commands(
            "yum update -y",
            "yum install -y httpd",
            "systemctl start httpd",
            "systemctl enable httpd",
            "echo '<h1>Hello from AWS CDK!</h1>' > /var/www/html/index.html"
        )

        # Step 8: Create outputs
        CfnOutput(
            self, "VPCId",
            value=vpc.vpc_id,
            description="VPC ID"
        )

        CfnOutput(
            self, "InternetGatewayId",
            value=vpc.internet_gateway_id,
            description="Internet Gateway ID"
        )

        CfnOutput(
            self, "PublicSubnetId",
            value=public_subnet.subnet_id,
            description="Public Subnet ID"
        )

        CfnOutput(
            self, "SecurityGroupId",
            value=security_group.security_group_id,
            description="Security Group ID"
        )

        CfnOutput(
            self, "EC2InstanceId",
            value=ec2_instance.instance_id,
            description="EC2 Instance ID"
        )

        CfnOutput(
            self, "EC2PublicIP",
            value=ec2_instance.instance_public_ip,
            description="EC2 Instance Public IP"
        )

        CfnOutput(
            self, "EC2PublicDNS",
            value=ec2_instance.instance_public_dns_name,
            description="EC2 Instance Public DNS"
        )

# Main app
app = App()

# You can specify your AWS account and region here
# env = Environment(account="123456789012", region="us-east-1")

InfrastructureStack(
    app, "InfrastructureStack",
    # env=env,  # Uncomment and modify if you want to specify account/region
    description="Complete AWS infrastructure with VPC, Subnet, IGW, Route Table, EC2, and Security Group"
)

app.synth()