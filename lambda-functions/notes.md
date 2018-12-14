# cloud functions development notes

## `lambda-tiler`
The `lambda-tiler` repo on Github uses `serverless` and Docker to deploy the rio-tiler library as a lambda function, and it's surprisingly great. Some interesting notes:
* They use `serverless`, but don't use the python packaging helper you can get for it. Instead they build within the `amazonlinux:latest` docker image the python environment, complete with handler code, and zip it into a zip file there. Then, they copy over the zip file and tell the serverless config to package it into the cloudformation template.
