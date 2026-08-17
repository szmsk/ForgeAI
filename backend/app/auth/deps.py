from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, set_tenant_context
from app.db.models import User, ApiKey
from app.auth.security import decode_access_token, hash_api_key
security=HTTPBearer(auto_error=False)

async def current_principal(creds: HTTPAuthorizationCredentials|None=Security(security), db:AsyncSession=Depends(get_db)):
    if not creds: raise HTTPException(401,'Authentication required')
    try: data=decode_access_token(creds.credentials)
    except Exception: raise HTTPException(401,'Invalid or expired token')
    await set_tenant_context(db,data['tenant_id'])
    user=await db.scalar(select(User).where(User.id==data['sub'],User.tenant_id==data['tenant_id'],User.is_active.is_(True)))
    if not user: raise HTTPException(401,'User not found')
    await set_tenant_context(db,user.tenant_id)
    return user

async def api_principal(creds: HTTPAuthorizationCredentials|None=Security(security), db:AsyncSession=Depends(get_db)):
    if not creds: raise HTTPException(401,'Authentication required')
    raw=creds.credentials
    if raw.startswith('fai_'):
        await db.execute(text("SELECT set_config('app.bootstrap','true',true)"))
        key=await db.scalar(select(ApiKey).where(ApiKey.key_hash==hash_api_key(raw),ApiKey.revoked.is_(False)))
        if key:
            await set_tenant_context(db,key.tenant_id)
            return key
    try: return await current_principal(creds,db)
    except HTTPException: raise HTTPException(401,'Invalid credentials')
