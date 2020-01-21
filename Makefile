deploy: image
	echo "push image...done."

image: sagemaker/credentials sagemaker/pytorch_p36.yml sagemaker/model
	docker build -f sagemaker/Dockerfile sagemaker

sagemaker/credentials:
	cp ~/.aws/credentials sagemaker/credentials

sagemaker/pytorch_p36.yml:
	cp environment/pytorch_p36.yml sagemaker/pytorch_p36.yml

sagamaker/model:
	cp -r model sagemaker/model
