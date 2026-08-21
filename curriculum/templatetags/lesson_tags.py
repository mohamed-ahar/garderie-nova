import re
from django import template

register = template.Library()

@register.filter
def replace_for_embed(url):
    if not url:
        return ""
    
    # Extraction de l'ID YouTube
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    
    if match:
        video_id = match.group(1)
        # On ajoute enablejsapi=1 et on enlève les restrictions qui causent l'erreur 153
        return f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&rel=0&origin=http://127.0.0.1:8000"
    
    return url