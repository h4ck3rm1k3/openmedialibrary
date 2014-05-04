websockets = []
nodes = False
main = None
online = False

def user():
    import settings
    import user.models
    return user.models.User.get_or_create(settings.USER_ID)
