from server import Http_status, Request, Router

status = Http_status()

def test_get(a1: int):
    print(a1)
    return {"a1":a1}, status.http_200()

def test_post(request: Request):
    print(request)
    return request, status.http_200()

def test_put(request: Request, a1: str):
    print("a1:",a1)
    print("req:",request)
    return {"a1": a1}, status.http_200()

def test_delete(a1: str, ):
    print(a1)
    return {"a1": a1}, status.http_200()

def test_patch( request: Request, a1: str):
    print(a1)
    print(request)
    return {"a1": a1}, status.http_200()



