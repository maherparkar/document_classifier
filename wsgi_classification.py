from flask_cookie_decode import CookieDecode
from app import app as application


SESSION_COOKIE_SECURE = True

if __name__ == "__main__":
    application.run()