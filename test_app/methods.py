from server import Http_status, Request, Router

status = Http_status()

def test_get(a1: str, a2: int, a3):
    return {"a1": a1, "a2": a2, "a3": a3}, status.http_200()

def test_post(request: Request):
    return request, status.http_200()

def test_put(a1: str, request: Request):
    print("a1:",a1)
    print("req:",request)
    return {"a1": a1}, status.http_200()

def test_delete(a1: str, ):
    print(a1)
    return {"a1": a1}, status.http_200()

def test_patch(a1: str, request: Request):
    print(a1)
    return {"a1": a1}, status.http_200()



