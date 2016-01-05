bandwidth = None
host = None
main = None
nodes = False
online = False
tasks = False
scraping = False
downloads = False
tor = False
websockets = []

activity = {}

def user():
    import settings
    import user.models
    return user.models.User.get_or_create(settings.USER_ID)

from threading import local
db = local()
