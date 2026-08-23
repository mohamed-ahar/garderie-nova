def theme(request):
    return {'theme': request.COOKIES.get('theme', 'light')}

def sidebar(request):
    return {
        'sidebar_state': request.COOKIES.get('sidebar', 'closed'),
        'open_section': request.COOKIES.get('open_section', '')
    }