websockets = []
nodes = False
tasks = False
main = None
online = False
host = None

activity = {}

def user():
    import settings
    import user.models
    return user.models.User.get_or_create(settings.USER_ID)
