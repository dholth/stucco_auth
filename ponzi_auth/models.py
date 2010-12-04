class Root(object):
    __name__ = ''

root = Root()

def get_root(request):
    return root
