from server import Server, Http_status
import test_app.router as app
status = Http_status()

api = Server(HOST="127.0.0.1", PORT=4201)
api.router.add_router(app.routes)

api.router.add_page("tavio","docs.html")

api.MAX_REQUEST_SIZE = 30
api.run()