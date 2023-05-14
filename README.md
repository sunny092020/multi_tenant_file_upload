# multi_tenant_file_upload

The purpose of this API is to allow multiple tenants to upload files to their respective accounts and link those files to specific resources and resource IDs.  
The API should support file upload, retrieval, deletion, listing, and filtering. The API is built using Django and PostgreSQL, and is deployed on EC2, with HTTPS provided by AWS API Gateway.

## steps how to provision the api

start an instance in EC2, t3a.micro, ubuntu server 22.04 TLS is recommended and
ssh into EC2 instance

pull the git

```
git pull https://github.com/sunny092020/multi_tenant_file_upload.git
cd multi_tenant_file_upload/multi_tenant_file_upload
```
install docker
```
sudo ./scripts/install_env.sh
```
build docker images
```
./scripts/build.sh
```

migrate db
```
./scripts/migrate.sh
```

run test
```
./scripts/test.sh
```

create some tenants to start manual testing, from john1 to john10
```
./script/init_data.sh
```

create a S3 bucket

define environment parameters in docker-compose.yml
```
- AWS_ACCESS_KEY_ID=<PLEASE_INPUT>
- AWS_SECRET_ACCESS_KEY=<PLEASE_INPUT>
- AWS_STORAGE_BUCKET_NAME=<PLEASE_INPUT>
- AWS_S3_REGION_NAME=<PLEASE_INPUT>
- DEBUG=False
```

start django api
```
./scripts/start.sh
```

create an AWS api gateway, which serves https from client and route request to our EC2 instance  
-Login to your AWS account  
-Move to API gateway service page  
-Click on "Create API" button  
-In "HTTP API" section, click "Build"  
-Click "Add integration"  
-In "Integrations" dropdown, choose HTTP  
-In "URL endpoint", input url endpoint of django deployed in EC2, for example:  
http://<YOUR_EC2_PUBLIC_DNS>:8000/{proxy}  
-Input your "API name", for example: mtfu  
-Click "Next"  
-In "Configure routes" page, In "Resource path", input "/{proxy+}"  
-Click "Next", and "Next"  
-Click "Create"  
-Now you see your api endpoint in "Invoke URL"  

Please setup securiry group of EC2 instance to allow incomming trafic from outside on port 8000
so the API gateway can connect on that port

# REST API Specification
This REST API is implemented in Django using the Django REST Framework.

## Upload File
`POST /upload`  
Uploads a file to Amazon S3 and creates a corresponding File object in the database.

### Request Parameters
file: `the file to be uploaded (multipart/form-data)`  
resource: `the resource associated with the file`  
resource_id: `the ID of the resource associated with the file`  
### Response
HTTP 200 OK: `the file was uploaded successfully`  
HTTP 400 Bad Request: `the request was malformed or the file upload failed`  
## Get Files
`GET /files/{resource}/{resourceId}?page={page}&page_size={page_size}`  
Gets all files associated with a given resource and resource ID, which belong to the user making request

### Request Parameters
resource: `the resource associated with the files`  
resourceId: `the ID of the resource associated with the files`  
page (optional): `page number`  
page_size (optional): `page size`
### Response
HTTP 200 OK: `a list of files associated with the resource and resource ID`  
HTTP 400 Bad Request: `the request was malformed or the files could not be retrieved`  
## Delete File
`DELETE /files/{resource}/{resourceId}`  
Deletes all files associated with a given resource and resource ID, which belong to the user making request

### Request Parameters
resource: `the resource associated with the files`  
resourceId: `the ID of the resource associated with the files`  
### Response
HTTP 200 OK: `the files were deleted successfully`  
HTTP 400 Bad Request: `the request was malformed or the files could not be deleted`  
## List Files
`POST /list_files`  
Gets all files associated with a specified tenant, resource, or resource ID.

### Request Parameters
tenant_username (optional): `the username of the tenant associated with the files`  
resource (optional): `the resource associated with the files`  
resource_id (optional): `the ID of the resource associated with the files`  
page (optional): `page number`  
page_size (optional): `page size`  
### Response
HTTP 200 OK: `a list of files associated with the specified parameters`  
HTTP 400 Bad Request: `the request was malformed or the files could not be retrieved`  

You can use curl to test the API, below is some examples:  

get your jwt token as john1
```
curl --location --request POST '<API_ENDPOINT>/api/token/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "john1",
    "password": "test"
}'
```
the response in the form of
{"refresh":"<REFRESH_TOKEN>","access":"<ACCESS_TOKEN>"}

you need to take the <ACCESS_TOKEN>

use the token to upload a file on behalf of john1
```
curl --location --request POST '<API_ENDPOINT>/api/upload' \
--header 'Authorization: Bearer <ACCESS_TOKEN>' \
--form 'file=@my_file' \
--form 'resource=product' \
--form 'resource_id=1'

curl --location --request POST '<API_ENDPOINT>/api/upload' --header 'Authorization: Bearer <ACCESS_TOKEN>' \
--form 'file=@my_file' \
--form 'resource=avatar' \
--form 'resource_id=1'
```

You can also retrieve files of yourself 
```
curl --location --request GET '<API_ENDPOINT>/api/files/product/1' --header 'Authorization: Bearer <ACCESS_TOKEN>'

curl --location --request GET '<API_ENDPOINT>/api/files/product/10' --header 'Authorization: Bearer <ACCESS_TOKEN>'

curl --location --request GET '<API_ENDPOINT>/api/files/product/2' --header 'Authorization: Bearer <ACCESS_TOKEN>'

curl --location --request GET '<API_ENDPOINT>/api/files/avatar/1' --header 'Authorization: Bearer <ACCESS_TOKEN>'

curl --location --request GET '<API_ENDPOINT>/api/files/2' --header 'Authorization: Bearer <ACCESS_TOKEN>'
```

You can also retrieve files by pagination
```
curl --location --request GET '<API_ENDPOINT>/api/files/product/1?page=2&page_size=5' --header 'Authorization: Bearer <ACCESS_TOKEN>'
```

You can also list files by pagination
```
curl --location --request POST '<API_ENDPOINT>/api/list_files' --header 'Authorization: Bearer <ACCESS_TOKEN>' \
--form 'resource=avatar' \
--form 'resource_id=1' \
--form 'page=1' \
--form 'page_size=3'
```

get your jwt token as john2
```
curl --location --request POST '<API_ENDPOINT>/api/token/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "john2",
    "password": "test"
}'
```
use the token to list files on behalf of john2
```
curl --location --request GET '<API_ENDPOINT>/api/files/product/1' --header 'Authorization: Bearer <ACCESS_TOKEN>'
```

## Design decisions:

Framework and tools:  
use Django because it is mature with security built-in, has many good features. The ORM is good to handle complex database scheme with many tables and relations. Query is very convinion
PostgreSQL for database is very reliable and can store files metadata well

Backend process deployment on EC2 t3a.micro is cost-effective  
AWS API Gateway can expose a https connection to client and route request to EC2 instance. It is also simple to deploy

Database schema: I designed a simple database schema with two tables: 
Tenant and File. 
```
Tenant
-username
-password

File
-tenant
-name
-location
-expiration date
-resource
-resource ID
-is_public
-delete_flg
```

Authentication and authorization: using JWT which is a popular standdard and can satisfy the need

Pagination: using Django Paginator module for pagination, which allows users to retrieve a subset of uploaded files based on a specified page number and size.

Connection to S3: use Boto3 library, which is the official library of AWS, so i think it is OK
