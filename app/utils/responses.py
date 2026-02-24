def success_response(msg, data=None, code=200):
    return {"status": "ok", "msg": msg, "data": data, "code": code}

def error_response(msg, code=400, data=None, errors=None):
    return {"status": "error", "msg": msg, "data": data, "errors": errors, "code": code}
