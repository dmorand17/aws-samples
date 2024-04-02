1. Export variables for CF stack

export MY_S3_BUCKET_NAME=domorand-872771682304
export MY_STACK_NAME=my-s3-bucket-stack

2. Create stack

MY_S3_BUCKET_NAME=xxxx MY_STACK_NAME=1111 cf-deploy-s3.sh

e.g. 
MY_S3_BUCKET_NAME=domorand-872771682304 MY_STACK_NAME=my-s3-bucket-stack ./cf-deploy-s3.sh

3. Copy file to bucket

aws s3 cp PVREOnboarding.zip s3://domorand-872771682304/
