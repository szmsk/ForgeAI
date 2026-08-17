from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
import hashlib, secrets, jwt
from app.core.config import settings
ph=PasswordHasher()

def hash_password(password:str)->str: return ph.hash(password)
def verify_password(password:str, hashed:str)->bool:
    try: return ph.verify(hashed,password)
    except Exception: return False

def create_access_token(user_id:str, tenant_id:str, role:str)->str:
    now=datetime.now(timezone.utc)
    return jwt.encode({'sub':user_id,'tenant_id':tenant_id,'role':role,'type':'access','iat':now,'exp':now+timedelta(minutes=settings.access_token_minutes)}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token:str)->dict:
    data=jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm])
    if data.get('type')!='access': raise ValueError('Invalid token type')
    return data

def new_api_key()->tuple[str,str,str]:
    raw='fai_'+secrets.token_urlsafe(32)
    return raw, raw[:12], hashlib.sha256(raw.encode()).hexdigest()

def hash_api_key(raw:str)->str: return hashlib.sha256(raw.encode()).hexdigest()
