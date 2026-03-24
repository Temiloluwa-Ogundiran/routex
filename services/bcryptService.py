import bcrypt

async def check_password(password:str, encrypted:str)->bool:
    """Checks if the password is valid"""
    return bcrypt.checkpw(password= password.encode('utf-8'), hashed_password= encrypted.encode('utf-8'))

async def make_password(password_string:str)->str:
    """Encrypts raw password and returns encryption"""
    return bcrypt.hashpw(password_string.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
