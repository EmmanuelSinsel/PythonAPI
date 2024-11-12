from server import Http_status, Request, Router

status = Http_status()

def test_get(dato_1: int):
    print(dato_1)
    return {"dato_1": dato_1}, status.http_200()


