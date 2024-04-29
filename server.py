import json
import os.path
import socket
import selectors
import threading
import types
from inspect import signature
from multiprocessing.sharedctypes import Value
import asyncio
import time
import sys
#from swagger_ui_bundle import swagger_ui_path


class Http_status:
    def http_200(self):
        return [b"200", b"OK"]

    def http_201(self):
        return [b"201", b"Created"]

    def http_204(self):
        return [b"204", b"No-Content"]

    def http_304(self):
        return [b"304", b"Not-Modified"]

    def http_400(self):
        return [b"400", b"Bad-Request"]

    def http_401(self):
        return [b"401", b"Unauthorized"]

    def http_403(self):
        return [b"403", b"Forbidden"]
    def http_404(self):
        return [b"404", b"Not-Found"]
    def http_405(self):
        return [b"405", b"Method-Not-Allowed"]

    def http_409(self):
        return [b"409", b"Conflict"]

    def http_410(self):
        return [b"410", b"Gone"]
    def http_413(self):
        return [b"413", b"Content-Too-Large"]

    def http_500(self):
        return [b"500", b"Internal-Server-Error"]
    def http_custom(self, status_code, status_text):
        return b"".join(status_code), b"".join(status_text)


class Router:
    prefix = None
    get_methods = {}
    get_methods_meta = {}
    post_methods = {}
    post_methods_meta = {}
    put_methods = {}
    put_methods_meta = {}
    delete_methods = {}
    delete_methods_meta = {}
    patch_methods = {}
    patch_methods_meta = {}
    page_urls = {}

    def __init__(self, prefix=None):
        self.prefix = prefix

    def __make_meta(self, function):
        params = signature(function)
        meta = []
        for i in params.parameters:
            meta.append({
                "name":params.parameters[i].name,
                "type":params.parameters[i].annotation
            })
        return meta

    def add_get(self, function, url: str, meta: list = None):
        if meta is None:
            meta = self.__make_meta(function)
        if self.prefix:
            url = self.prefix+"/"+url
        self.get_methods[url] = function
        self.get_methods_meta[url] = meta

    def add_post(self, function, url: str, meta: list = None):
        if meta is None:
            meta = self.__make_meta(function)
        if self.prefix:
            url = self.prefix+"/"+url
        self.post_methods[url] = function
        self.post_methods_meta[url] = meta

    def add_put(self, function, url: str, meta: list = None):
        if meta is None:
            meta = self.__make_meta(function)
        if self.prefix:
            url = self.prefix+"/"+url
        self.put_methods[url] = function
        self.put_methods_meta[url] = meta

    def add_delete(self, function, url: str, meta: list = None):
        if meta is None:
            meta = self.__make_meta(function)
        if self.prefix:
            url = self.prefix+"/"+url
        self.delete_methods[url] = function
        self.delete_methods_meta[url] = meta

    def add_patch(self, function, url: str, meta: list = None):
        if meta is None:
            meta = self.__make_meta(function)
        if self.prefix:
            url = self.prefix+"/"+url
        self.patch_methods[url] = function
        self.patch_methods_meta[url] = meta

    def add_page(self, url, file):
        if self.prefix:
            url = self.prefix+"/"+url
        self.page_urls[url] = file

    def add_router(self, router):
        self.get_methods.update(router.get_methods)
        self.post_methods.update(router.post_methods)
        self.put_methods.update(router.put_methods)
        self.delete_methods.update(router.delete_methods)
        self.patch_methods.update(router.patch_methods)
        self.page_urls.update(router.page_urls)

class Server():
    __DOCS_URL = "docs"
    __METHODS: Router
    __HOST = ""
    __PORT = 0
    __CHUNK_SIZE = 1024

    sel = selectors.DefaultSelector()
    router = Router()

    status_codes = Http_status()
    error_status = [
        status_codes.http_404(),
        status_codes.http_400()
    ]
    MAX_REQUEST_SIZE = 0.25

    request_types = ["POST", "GET", "PATCH", "DELETE", "PUT", "OPTIONS", "HEAD"]
    no_ssl = "PGDOH"

    def __init__(self, HOST: str, PORT: int, ts: bool = False):
        self.__HOST = HOST
        self.__PORT = PORT
        print("Initialized server on "+HOST+":"+str(PORT))
        if ts == True:
            print("ALBUMES DE LA TAYLOR SWISS:")
            print("1 - Taylor Swift")
            print("2 - Fearless")
            print("3 - Speak Now ")
            print("4 - Red")
            print("5 - 1989")
            print("6 - Reputation ")
            print("7 - Lover")
            print("8 - Folklore")
            print("9 - Evermore")
            print("10 - Midnights")
            print("11 - The Tortured Poets Department")

    def swagger(self):
        spec_string = '{"openapi":"3.0.1","info":{"title":"python-swagger-ui test api","description":"python-swagger-ui test api","version":"1.0.0"},"servers":[{"url":"http://127.0.0.1:8989/api"}],"tags":[{"name":"default","description":"default tag"}],"paths":{"/hello/world":{"get":{"tags":["default"],"summary":"output hello world.","responses":{"200":{"description":"OK","content":{"application/text":{"schema":{"type":"object","example":"Hello World!!!"}}}}}}}},"components":{}}'
        #api_doc(app, config_spec=spec_string, url_prefix='/api/doc', title='API doc')

    # SE ENCARGA DE ENVIAR LA RESPUESTA AL CLIENTE
    def sender(self, s: socket, body: str, status: []):
        body_raw = json.dumps(body)
        headers = {
            'Content-type': 'application/json; charset=UTF-8',
            'content-length': len(body_raw),
            'connection': 'close',
        }
        headers_raw = ''.join('%s: %s\n' % (k, v) for k, v in headers.items())
        response_proto = b'HTTP/1.1'
        response_status = status[0]
        response_status_text = status[1]
        s.send(b'%s %s %s' % (response_proto, response_status, response_status_text))
        s.send(b'\n')
        s.send(bytes(headers_raw, 'utf-8'))
        s.send(b'\n')
        s.send(bytes(body_raw, 'utf-8'))

    def senderHtml(self, s: socket, body, status: []):

        response_proto = b'HTTP/1.1'
        response_status = status[0]
        response_status_text = status[1]
        s.send(b'%s %s %s' % (response_proto, response_status, response_status_text))
        s.send(b'\n\n')
        s.send(bytes(body, 'utf-8'))

    # ACCEPTA LAS CONEXIONES A LOS SOCKETS
    def accept_wrapper(self, sock):
        conn, addr = sock.accept()
        conn.setblocking(True)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    # SE ENCARGA DE RECIBIR LAS PETICIONES Y ENRUTARLAS AL CONSTRUCTOR DE PETICIONES
    # Y POSTERIORMENTE AL MANEJADOR PARA SER LLAMADAS

    def get_msg_len(self, recv_data):
        header_type = str(recv_data, 'UTF8')[0:7]
        header_type = header_type[:header_type.find(' ')]
        msg_size = 0
        if header_type in self.request_types:
            headers = str(recv_data, 'UTF8').replace('\n', '').replace(' ', '').split("\r")
            for i in headers:
                if 'Content-Length' in i:
                    data = i.split(":")
                    return data[1]
        return None

    def get_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        data_dict = vars(data)
        if mask & selectors.EVENT_READ:              # INICIALIZA LA VARIABLE QUE ALMACENA EL MENSAJE RECIBIDO
            chunks = []                              # LISTA QUE ALMACENA LOS TROZOS DEl BODY
            bytes_recd = 0                           # CONTADOR DE LOS BYTES RECIBIDOS
            msg_len = 0
            chunk = sock.recv(1024)
            chunks.append(chunk)
            msg_len = self.get_msg_len(chunk)
            if msg_len is not None:
                msg_len = int(msg_len)
                if len(chunk) == 1024:
                    while bytes_recd < msg_len:
                        chunk = sock.recv(min(msg_len - bytes_recd, self.__CHUNK_SIZE))  # LEE UN TROZO DE 2048 BYTES DEL MENSAJE
                        if not chunk:
                            raise RuntimeError("ERROR")
                        chunks.append(chunk)             # GUARDA EL TROZO EN LA LISTA CHUNKS
                        bytes_recd += len(chunk)         # SUMA LOS BYTES RECIBIDOS
                        if len(chunk)<self.__CHUNK_SIZE and msg_len - bytes_recd < self.__CHUNK_SIZE:
                            break
            recv_data = b"".join(chunks)         # SUMA TODOS LOS TROZOS EN UNA CADENA DE BYTES

            if msg_len is not None:
                if int(msg_len) > (self.MAX_REQUEST_SIZE*pow(1024,2)):
                    body = {"Message": "Content Too Large",
                            "Content-Lenght": msg_len,
                            "Max-Content-Lenght": (self.MAX_REQUEST_SIZE*pow(1024,2))
                            }
                    self.sender(sock, body, self.status_codes.http_413())
                    self.sel.unregister(sock)
                    sock.close()
                    return
            #A PARTIR DE AQUI SI JALA
            str_recv_data = str(recv_data, 'UTF8')
            raw = str_recv_data.split("\r\n\r\n")
            if (str_recv_data != ''):
                rtype, params = self.request_constructor(data_dict['addr'][1], raw)
                if params != None:
                    suburl = self.get_url(params)
                    print(suburl)
                    if suburl[0] not in self.__METHODS.page_urls:
                        run, status = self.handle_request(rtype, suburl, params)
                        if status not in self.error_status:
                            print(rtype,"REQUEST ACCEPED FROM",data_dict['addr'],"- STATUS:",status[0].decode("utf-8"),status[1].decode("utf-8"))
                            self.sender(sock, run, status)
                        else:
                            print(rtype,"REQUEST FAILED FROM", data_dict['addr'],"- STATUS",status[0].decode("utf-8"),"ERROR -",run)
                    else:
                        url = suburl[0]
                        if os.path.isfile("htdocs/" + url):
                            content = open("htdocs/" + url).read()
                            self.senderHtml(sock, content , self.status_codes.http_201())
                        elif url in self.router.page_urls:
                            content = open("htdocs/" + self.router.page_urls[url]).read()
                            self.senderHtml(sock, content, self.status_codes.http_201())
                        else:
                            self.senderHtml(sock, '', self.status_codes.http_404())
                    self.sel.unregister(sock)
                    sock.close()
                    return
            if recv_data:
                data.outb += recv_data

    def handle_request_html(self, suburl):
        return self.__METHODS.page_urls[suburl], self.status_codes.http_201()

    # MANEJA LA LLAMADA A EL METODO ESPECIFICADO EN LA URL Y SU ESTATUS
    def handle_request(self, rtype, suburl, params):
        run = None
        status = None
        try:
            if suburl[0] == self.__DOCS_URL:
                return open("docs.html").read(), self.status_codes.http_201(), 0
            if len(suburl[0]) > 1:
                if rtype == "GET":
                    args = self.url_paramters(params=suburl[1],
                                              function=self.__METHODS.get_methods[suburl[0]],
                                              meta=self.__METHODS.get_methods_meta[suburl[0]])
                    if args == None:
                        run, status = self.__METHODS.get_methods[suburl[0]]()
                    else:
                        run, status = self.__METHODS.get_methods[suburl[0]](**args)
                    if run == None:
                        return "Not found", self.status_codes.http_404()
                    return run, status
                if rtype == "POST":
                    params[1] = params[1].replace("\n", '')
                    request = json.loads(params[1])
                    if suburl[0] not in self.__METHODS.post_methods:
                        return "'"+suburl[0]+"' Not found", self.status_codes.http_404()
                    run, status = self.__METHODS.post_methods[suburl[0]](request)
                    return run, status
                if rtype == "PUT":
                    params[1] = params[1].replace("\n", '')
                    request = json.loads(params[1])
                    args = self.url_paramters(params=suburl[1],
                                              function=self.__METHODS.put_methods[suburl[0]],
                                              request=params[1],
                                              meta=self.__METHODS.put_methods_meta[suburl[0]])
                    run, status = self.__METHODS.put_methods[suburl[0]](request, **args)
                    if run == None:
                        return "Not found", self.status_codes.http_404()
                    return run, status
                if rtype == "DELETE":
                    params = self.url_paramters(params=suburl[1],
                                                function=self.__METHODS.delete_methods[suburl[0]],
                                                meta=self.__METHODS.delete_methods_meta[suburl[0]])
                    run, status = self.__METHODS.delete_methods[suburl[0]](**params)
                    if run == None:
                        return "Not found", self.status_codes.http_404()
                    return run, status
                if rtype == "HEAD":
                    pass
                if rtype == "OPTIONS":
                    pass
                if rtype == "PATCH":
                    params[1] = params[1].replace("\n", '')
                    request = json.loads(params[1])
                    args = self.url_paramters(params=suburl[1],
                                              function=self.__METHODS.patch_methods[suburl[0]],
                                              request=params[1],
                                              meta=self.__METHODS.patch_methods_meta[suburl[0]])
                    run, status = self.__METHODS.patch_methods[suburl[0]](request, **args)
                    if run == None:
                        return "Not found", self.status_codes.http_404()
                    return run, status
            else:
                return 'not allowed', self.status_codes.http_404(), 1
        except Exception as err:
            print("ERROR "+str(err))
            return err, self.status_codes.http_400()

    def url_paramters(self, params: str, function, meta,  request: str = ""):
        try:
            method_params = params.split("&")
            params = []
            for i in range(len(method_params)):
                temp = method_params[i].split("=")
                params.append([meta[i]['name'], temp[1]])
            data = {}
            for arg in meta:
                arg_name = str(arg['name'])
                arg_type = str(arg['type'])
                p = -1
                for j in range(len(params)):
                    if params[j][0] == arg_name:
                        p = j
                        break
                if p == -1:
                    data[arg_name] = json.loads(request)
                if 'str' in arg_type:
                    params[p][1] = params[p][1].replace("'", '')
                    data[arg_name] = str(params[p][1])
                if 'int' in arg_type:
                    data[arg_name] = int(params[p][1])
                if 'float' in arg_type:
                    data[arg_name] = float(params[p][1])
                if 'bool' in arg_type:
                    data[arg_name] = bool(params[p][1])
                if 'list' in arg_type:
                    t = []
                if 'tuple' in arg_type:
                    t = ()
                if 'dict' in arg_type:
                    t = {}
                if 'bytes' in arg_type:
                    t = b''
                if 'inspect._empty' in arg_type:
                    params[p][1] = params[p][1].replace('"', '')
                    params[p][1] = params[p][1].replace("'", '')
                    data[arg_name] = self.guess_type(params[p][1])
            return data
        except Exception as err:
            print(err)
            return None

    # SE ENCARGA DE TOMAR LA URL DEL METODO QUE DEBE SER LLAMADO
    def get_url(self, params):
        params = params[0].split("\n")
        url = params[0].split(" ")
        suburl = url[1][1:]
        if "?" not in suburl:
            suburl = [suburl, ""]
        else:
            suburl = suburl.split("?")
        return suburl

    # SE ENCARGA DE ENSAMBLAR LAS PETICIONES QUE CONSTAN DE MAS DE UN MENSAJE,
    # LAS DE UN SOLO MENSAJE LAS PASA COMO LISTA

    def request_constructor(self, port: str, raw: list):
        if "POST" in raw[0]:
            full_raw = [raw[0],raw[1]]
            return "POST", full_raw
        if "GET" in raw[0]:
            return "GET", [raw[0]]
        if "PATCH" in raw[0]:
            full_raw = [raw[0],raw[1]]
            return "PATCH", full_raw
        if "DELETE" in raw[0]:
            return "DELETE", [raw[0]]
        if "PUT" in raw[0]:
            full_raw = [raw[0],raw[1]]
            return "PUT", full_raw
        if "HEAD" in raw[0]:
            return "HEAD", [raw[0]]
        if "OPTIONS" in raw[0]:
            return "OPTIONS", [raw[0]]

    def guess_type(self, var):
        var = str(var)
        try:
            var = int(var)
            return var
        except ValueError:
            pass
        try:
            var = float(var)
            return var
        except ValueError:
            pass
        try:
            if var == 'True':
                return True
            if var == 'False':
                return False
        except ValueError:
            pass
        return var

    # MANEJADOR DE LAS PETICIONES
    def run(self):
        self.swagger()
        self.__METHODS = self.router
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.__HOST, self.__PORT))
            s.listen()
            s.setblocking(False)
            self.sel.register(s, selectors.EVENT_READ, data=None)
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.get_connection(key,mask)

# CLASE QUE ALMACENA TODOS LOS METODOS DE LA API, LOS CUALES POSTERIORMENTE SE DAN AL SERVIDOR EN SU CONSTRUCTOR

class Request:
    pass