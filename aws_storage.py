import json
import requests, logging, boto3
from boto3 import Session
from botocore.exceptions import ClientError


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)

    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response


# noinspection PyComparisonWithNone
class Bucket():
    def __init__(self, bucket_name, directory : str = ''):
        self.bucket_name = bucket_name
        self.directory = directory

    def upload(self, object_name : str, return_url : True, file=None):
        response = create_presigned_post(self.bucket_name, self.directory +  object_name)

        if file == None:
            with open(object_name, 'rb') as f:
                files = {'file': (object_name, f)}
                http_response = requests.post(response['url'], data=response['fields'], files=files)
        else :
            files = {'file': (object_name, file)}
            http_response = requests.post(response['url'], data=response['fields'], files=files)

        logging.info(f'File upload HTTP status code: {http_response.status_code}')
        if return_url: return create_presigned_url(self.bucket_name, object_name)

    def getLink(self, object_name : str, expiration : 3600) -> str:
        return create_presigned_url(self.bucket_name, self.directory + object_name, expiration=expiration)
 
    def Download(self, object_name : str) -> dict:
        url = self.getLink(object_name, expiration=20)
        r = requests.get(url, allow_redirects=True)
        return json.loads(r.content)

    def GetUploadPost(self, object_name : str, expiration : 3600, conditions = None) -> dict:
        return create_presigned_post(self.bucket_name, self.directory + object_name, expiration=expiration, conditions=conditions)

    def Exists(self, object_name : str) -> bool:
        s3 = Session()
        s3_client = s3.resource("s3")
        obj = s3_client.Object(self.bucket_name, self.directory +  object_name)
        
        try :
            obj.last_modified
        except:
            return False
        return True
    
    def GetAllObjects(self) -> dict:
        client = boto3.client('s3')
        result = client.list_objects_v2(Bucket=self.bucket_name, Prefix=self.directory, MaxKeys=100, Delimiter='/')
        results = {}
        if result == None:
            return results
        if result.get('CommonPrefixes') == None:
            return results
        for o in result.get('CommonPrefixes'):
            results[len(results) + 1] = o.get('Prefix').removeprefix(self.directory).removesuffix('/')
        return results


    def CreateFolder(self, directory : str):
        """Creates a new folder. (do not put '/' at the end of the directory string)\n\n Bucket.CreateFolder('test') will create a new empty folder at the root directory named test."""
        s3_client = boto3.client('s3')
        s3_client.put_object(Bucket=self.bucket_name, Key=(self.directory+directory+'/'))

    def Remove(self, object_name : str):
        s3 = Session()
        s3_client = s3.resource("s3")
        obj = s3_client.Object(self.bucket_name, self.directory + object_name)
        obj.delete()
