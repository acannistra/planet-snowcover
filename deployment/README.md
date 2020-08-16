<p>
  <h1> AWS Cloud Infrastructure Deployment via Terraform
  <img width=60 style="float: right;" src="https://www.terraform.io/assets/images/og-image-8b3e4f7d.png"></h1></p>

🚨**WARNING**🚨: The steps in this tutorial ***may result in charges*** to your AWS account. Always backup your work and **`terraform destroy`** when you're done working to avoid unnecessary charges.

For better or worse, this project relies upon a nontrivial amount of Amazon Web Services cloud infrastructure. While these resources are relatively simple, they require some know-how to set up in a way that makes them convenient and easy-to-use. This configuration is somewhat unpleasant.

Fortunately there are tools that allow us to specify exactly which resources we'd like to use, and can set up those resources for us. One of these tools is known as [**Terraform**](https://www.terraform.io/docs/), and we'll use this one to setup our infrastructure.

## 💻 Installing Terraform

The best way to install Terraform is to follow their [**Installation Guide**](https://learn.hashicorp.com/terraform/getting-started/install.html). The process involves downloading the latest version of the software to your computer and unzipping it. It's pretty straightforward.

Once you do that, you should be able to run `terraform` on the command line and see some output.

Before we deploy any infrastructure, we need to set up your local environment so that Terraform knows which accounts to use in deploying these resources.

## 🔐 Configuring AWS + SSH

There's some preparation that we need to do to be able to deploy our infrastructure. You'll need to have **configured AWS credentials** with correct permissions and **configured an SSH key**. These steps will detail how to do that.

### **Configure AWS (Personal Account)**

Follow these steps if you've never created an AWS account before or if you are a qualified administrator of an AWS account.

1. **Sign up for AWS.** To perform this configuration, be sure you have an AWS account. If you don't, [go here](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) and follow the instructions.
1. **Install the AWS Command Line Tools**. For this tutorial, you'll need to install the AWS CLI tools. If you have `pip` installed, run the following command to install them:

        pip3 install awscli --upgrade --user

3. **Create AWS Credentials**: To sign in to AWS from the CLI, you need an *AccessKey* and *SecretKey* pair. Follow the instructions listed on AWS's documentation [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) to configure access keys. ⚠️**Note**⚠️ that you can only download your secret key once –– if you misplace it, you'll need to create another.
3. **Sign In with your AWS Credentials**. Once you've installed the AWS cli and configured keys in the AWS console, run `aws configure` to configure the CLI with your credentials.

### **Configure AWS (Group/Shared Account)**

Follow these steps if you're a delegated IAM user of a shared AWS account.

1. **Ask your administrator to update your account policy**. Deploying the resources required to run the code in this project requires a somewhat broad set of permissions. In particular, we require access to the following services: EC2, SageMaker, and S3, as well as some specific IAM permissions. To facilitate this, we provide [`aws_userpolicy.json`](./aws_userpolicy.json), which contains a broad set of permissions that will allow for infrastructure deployment. Please send this policy to your administrator and ask for it to be attached to your account.
1. **Follow steps 2-4 Above**. Now that you've been properly credentialed, you can install the AWS command line toole, create some credentials, and sign-in.




### Configure your SSH Keys

To connect to AWS resources, you need to identify who you are. The way we do this is through "SSH keys". You can think of them as exactly that: keys that allow access.

You create a key, and provide it to AWS when you create your cloud resources. When you go to access those resources, you provide a key. AWS will check to see if it's the same key that you provided upon creation; if it is, you'll be granted access.

We'll create a key now. *(If you already have an SSH key, you can skip this)*.

Run the following on the command line:

    ssh-keygen -t rsa -b 4096

You'll be asked a series of questions. The most important to note is

    Enter a file in which to save the key (/Users/you/.ssh/id_rsa): [Press Enter]

You can just press enter to accept this default, but be sure to note the path that the key is stored in (something like `/Users/you/.ssh/id_rsa`). We need it later. No need to set a passphrase for your key, they're secure without it.

This process creates two files: `id_rsa` (your *private key*), and `id_rsa.pub` (your *public key*). We'll need both files. Be sure to keep your private key safe, as it allows anyone access. You can share your public key.

Now we're ready to configure Terraform.

## 🗒Configuring Terraform

We've created a `variables.tf` file to keep track of all of the settings required for Terraform to successfuly deploy these resources. You'll edit this file with the information you've just generated above.  

Find the `variables.tf` file in this directory and open it in your favorite text editor. At the top, you'll see the following:

```
variable "aws_profile" {
  default = "default"
}

variable "public_key" {
  description = "Public key path"
  default = "~/.ssh/id_rsa.pub"
}

variable "private_key" {
  default = "~/.ssh/id_rsa"
}
```

Here's some guidance on how to set these variables:

| Variable  | Recommended Setting | Notes |
|---|---|---|
|  `aws_profile` | **`default`**, unless you setup a named profile in `aws configure`.  | To check if you have a named profile, take a look at your `~/.aws/credentials` file in your home directory.  |
|  `public_key` | `~/.ssh/id_rsa.pub`  | Again, unless you specified a different path to `ssh-keygen` above, your path will be `~/.ssh/id_rsa.pub`.  |
|  `private_key` | `~/.ssh/id_rsa`  | Same as above. |

## 🌪🆙 Deploying Compute Infrastructure.

The final step in this process is to inspect and deploy the AWS infrastructure components. Be sure to `cd` into *this directory* (`planet-snowcover/deployment`) before running these commands.

  First, we need to make sure Terraform has the right plugins installed to work with AWS. Running

      terraform init

should install the correct plugins. Then, run

    terraform plan

to see a list of the cloud resources which will be created in the next step. To most, this won't be a terribly meaningful list. However, if you're interested in the deployment configuration, check out the plan (and the `resource.tf` file in this directory).

Finally, to deploy these resources, run

    terraform apply

This process will ask you for confirmation (type `yes`), and will talk to AWS to configure the cloud compute resources we need to do this work. It should take about 20 minutes.

When it's complete, you should see an output looking something like this:

    Outputs:

    public_instance_ip = [
    "XXX.XXX.XXX.XXX",
    ]

    SSH_CMD = "ssh -i /path/to/key.pem ubuntu@$XXX.XXX.XXX.XXX"

    sagemaker_role_arn = "arn:aws:sagemaker:xxxxx"

Importantly, the `SSH_CMD` value is a command which will connect you to the newly-deployed EC2 instance. You'll also need the `sagemaker_role_arn` value for model training.

## Login + Start JupyterLab

The output of `terraform apply` (which is always available by running `terraform output`), is both an IP adress and a command which can be used to SSH into a newly-deployed EC2 instance. This instance has been provisioned with a Docker image containing JupyterLab, our tutorial and development environment. Follow these steps to launch JupyterLab.

1. SSH into the instance: `eval $(terraform output SSH_CMD)` or copy/paste the SSH_CMD value above.
1. Once logged-in, run `sudo docker run -ti -p 8888:8888 -v $(pwd):/host tonycannistra/planet-snowcover lab`. This should produce output with a URL like: `http://0.0.0.0:8888/?token=4715df79c9b1c97244618552e2198ba478cd42f3fa5ebbd8`.
1. In your browser, paste the value of `public_instance_ip` from `terraform output` as follows: `XXX.XXX.XXX.XXX:8888`. In the box, copy and paste the value after `token` in the above URL and press Enter.

**TODO: add smarter volume mounting + git pull of tutorials**

## IMPORTANT: Turn off your instances *every time*.

As mentioned above, this deployment comes with a monthly fee, as does every Amazon resource. To save money, **shut down your EC2 instance when you're done using it**. If you wish to return to your work, do not `terminate` the instance.

If you don't have any saved work and would like to destroy all of the deployed resources, run `terraform destroy`. All unsaved work stored in any of the deployed resources (EC2, mainly) will be lost. 

## Appendix: Provisioned Resources

This terraform configuration will create (and therefore can destroy) the following resources:

* AWS Elastic Container Repository repo (name: `ps-images`)
* EC2 Virtual Private Cloud
* EC2 Internet Gateway
* EC2 subnet within the VPC
* EC2 network routing table within the VPC for global access from all IPs
* EC2 security group with ports 22/80/8888 ingress and * egress
* EC2 public key
* IAM role for EC2 access to services
* IAMPo asfzlicyAttachment to above IAM role (policy specified in `variables.tf`)
* **EC2 Instance** (name: `mainDevInstance`), provisioned with:
  * local public SSH key for access (*via `file` provisioner*)
  * Development docker image from DockerHub (specified in `variables.tf`), which is pushed to the newly-created `ps-images` ECR repo (*via `remote-exec` provisioner*)
* IAM role for SageMaker to access AWS account resources (S3).
* IAMPolicyAttachment to attach specific resource access to above role
