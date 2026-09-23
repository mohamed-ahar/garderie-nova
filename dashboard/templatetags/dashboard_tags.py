from django import template

register = template.Library()


@register.filter
def div(value, arg):
    """
    Divide the value by the argument.
    Usage: {{ value|div:arg }}
    """
    try:
        value = int(value)
        arg = int(arg)
        if arg == 0:
            return 0
        return value // arg
    except (ValueError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def get_item(dictionary, key):
    """
    Returns the value of a dictionary given a key.
    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)