import pulumi
import pulumi_aws as aws
# https://github.com/pulumi/pulumi-docker
import pulumi_docker as docker # https://www.pulumi.com/registry/packages/docker/
import pulumi_kubernetes as k8s

# # Fetch the default VPC because we cannot connect directly to the EKS cluster
# # This is because bridge networks (for DNS) don't integrate well with EKS, which a vpc does
# default_vpc = aws.ec2.get_vpc(default=True)

# # Get all subnets to map VPC to the docker network
# # https://www.pulumi.com/registry/packages/aws/api-docs/ec2/getsubnets/
# all_subnets = aws.ec2.get_subnets()
# subnets = all_subnets.ids

vpc = aws.ec2.Vpc("vpc", cidr_block="172.31.0.0/16")
subnet = aws.ec2.Subnet("subnet", vpc_id=vpc.id, cidr_block="172.31.1.0/24")

# Create an AWS EKS cluster
# IAM roles here are written so that worker nodes can figure out which EKS API to connect to
eks_cluster = aws.eks.Cluster("eksCluster", 
    role_arn=aws.iam.Role("eksRole",
        assume_role_policy='''{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "eks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }''').arn,
    vpc_config=aws.eks.ClusterVpcConfigArgs(
        # subnet_ids=subnets,  # Use discovered subnets here
        vpc_id=vpc.id,
        subnet_ids=[subnet.id],
        public_access_cidrs=["0.0.0.0/0"],
        endpoint_public_access=True,
    )
)

# Define the Docker build for the static website
static_website_image = docker.Image("staticWebsiteImage",
  build=docker.DockerBuildArgs(
    context=".",
    dockerfile="Dockerfile"
  ),
  image_name="my-static-website",
  skip_push=False  
)

# # Reference pre-built Docker image
# static_website_image = docker.Image("staticWebsiteImage",
#   image_name="my-static-website:v1.0.0"  
# )

# Deploy the website as a Kubernetes Deployment
app_labels = {"app": "static-website"}
static_website_deployment = k8s.apps.v1.Deployment("staticWebsiteDeployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        labels=app_labels,
        namespace="default",
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=app_labels),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(labels=app_labels),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[k8s.core.v1.ContainerArgs(
                    name="static-website-container",
                    image=static_website_image.image_name,
                )],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[eks_cluster]
    )
)

# Export the EKS cluster kubeconfig
pulumi.export("kubeconfig", eks_cluster.kubeconfig)