def success_response(msg, data=None):
    return {"status": "ok", "msg": msg, "data": data }

def error_response(msg, data=None, errors=None):
    return {"status": "error", "msg": msg, "data": data, "errors": errors }