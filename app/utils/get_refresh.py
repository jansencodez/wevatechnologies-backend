from fastapi import HTTPException, Request

def get_refresh_token_from_cookie(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing")
    
    return refresh_token
