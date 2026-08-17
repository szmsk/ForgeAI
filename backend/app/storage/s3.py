from __future__ import annotations
import io, tarfile, uuid
from pathlib import Path
import boto3
from botocore.client import Config
from app.core.config import settings

class ArtifactStore:
    def __init__(self):
        kwargs={'region_name':settings.s3_region,'aws_access_key_id':settings.s3_access_key,'aws_secret_access_key':settings.s3_secret_key,'config':Config(signature_version='s3v4')}
        if settings.s3_endpoint: kwargs['endpoint_url']=settings.s3_endpoint
        self.client=boto3.client('s3',**kwargs)
    def put_repo(self,root:Path,run_id:str)->str:
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as tar: tar.add(root,arcname='repo')
        buf.seek(0); key=f'runs/{run_id}/repo.tar.gz'; self.client.put_object(Bucket=settings.artifact_bucket,Key=key,Body=buf.getvalue(),ContentType='application/gzip'); return key
    def presign_get(self,key:str,seconds:int=900)->str: return self.client.generate_presigned_url('get_object',Params={'Bucket':settings.artifact_bucket,'Key':key},ExpiresIn=seconds)
    def presign_put(self,key:str,seconds:int=900)->str: return self.client.generate_presigned_url('put_object',Params={'Bucket':settings.artifact_bucket,'Key':key},ExpiresIn=seconds)
    def get_bytes(self,key:str)->bytes: return self.client.get_object(Bucket=settings.artifact_bucket,Key=key)['Body'].read()
