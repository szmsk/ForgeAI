from enum import Enum
from pydantic import BaseModel, Field
class RunStatus(str,Enum): queued='queued'; running='running'; success='success'; failed='failed'; stopped='stopped'
class RegisterRequest(BaseModel): email:str; password:str=Field(min_length=12,max_length=128); tenant_name:str=Field(min_length=2,max_length=160)
class LoginRequest(BaseModel): email:str; password:str
class TokenResponse(BaseModel): access_token:str; token_type:str='bearer'; expires_in:int
class RunRequest(BaseModel): repository:str=Field(default='demo://calculator',min_length=1,max_length=2000); task:str=Field(min_length=5,max_length=12000); max_iterations:int=Field(default=5,ge=1,le=8); max_seconds:int=Field(default=120,ge=5,le=600); create_pr:bool=False; base_branch:str|None=None
class Event(BaseModel): type:str; message:str; iteration:int=0; metadata:dict=Field(default_factory=dict); timestamp:str|None=None
class RunResponse(BaseModel): id:str; status:RunStatus; repository:str; task:str; events:list[Event]; files_changed:list[str]; tests_passed:int; tests_total:int; iterations:int; duration_ms:int; cost_usd:float; input_tokens:int=0; output_tokens:int=0; pull_request_url:str|None=None; summary:str
class RunAccepted(BaseModel): id:str; status:RunStatus
class HealthResponse(BaseModel): status:str; service:str; version:str; dependencies:dict
class ApiKeyCreate(BaseModel): name:str=Field(min_length=2,max_length=120)
class ApiKeyResponse(BaseModel): id:str; name:str; prefix:str; key:str
