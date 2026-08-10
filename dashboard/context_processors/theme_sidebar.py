def theme(request):
    return {'theme': request.COOKIES.get('theme', 'light')}

def sidebar(request):
    return {'sidebar_state': request.COOKIES.get('sidebar', 'closed')}