from django import template
import re

register = template.Library()

@register.filter(name='replace_for_embed')
def replace_for_embed(value):
    """
    Kiy-transformi YouTube URL l-Embed URL
    Ex: https://www.youtube.com/watch?v=ID -> https://www.youtube.com/embed/ID
    """
    if not value:
        return ""
    
    # RegEx bach n-jbdou l-Video ID
    reg = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(reg, value)
    
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    
    return value