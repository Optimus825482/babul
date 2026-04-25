from flask_cors import CORS


cors = CORS()


class _NoopDB:
    def init_app(self, app):
        return None

    def create_all(self):
        return None


db = _NoopDB()
