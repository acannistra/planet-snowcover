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

There's some preparation that we need to do to be able to deploy our infrastructure. You'll need to have **configured AWS credentials** and **configured an SSH key**. These steps will detail how to do that.

### **Configure AWS**:

1. **Sign up for AWS.** To perform this configuration, be sure you have an AWS account. If you don't, [go here](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) and follow the instructions.
1. **Install the AWS Command Line Tools**. For this tutorial, you'll need to install the AWS CLI tools. If you have `pip` installed, run the following command to install them:

        pip3 install awscli --upgrade --user

3. **Create AWS Credentials**: To sign in to AWS from the CLI, you need an *AccessKey* and *SecretKey* pair. Follow the instructions listed on AWS's documentation [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) to configure access keys. ⚠️**Note**⚠️ that you can only download your secret key once –– if you misplace it, you'll need to create another.
3. **Sign In with your AWS Credentials**. Once you've installed the AWS cli and configured keys in the AWS console, run `aws configure` to configure the CLI with your credentials.



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

This process will ask you for confirmation (type `yes`), and will talk to AWS to configure the cloud compute resources we need to do this work. It should take less than 5 minutes.

When it's complete, you should see an output looking something like this:

    Outputs:

    public_instance_ip = [
    "35.160.4.86",
    ]
    public_route_table_ids = [
    "rtb-08ef3ffbecd7f07ae",
    ]
    public_subnets = [
    "subnet-08b663ab9282029fe",
    ]
    vpc_id = vpc-052b4f723bcd819ce

The most important piece of information to note here is **`public_instance_ip`**, which is the address of our newly deployed cloud computer.

## Accessing Resources + Deploying Jupyter Lab

***TODO: Finish this section***
