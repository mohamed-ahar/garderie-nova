from datetime import date

def calculate_ratio_stats(present_children, all_children=None):
    """
    Calculates ratio statistics for a list of children.
    Logic mirrored from Group.recalculate_ratios in models.py
    
    present_children: Children currently marked as 'in'
    all_children: All children in the category (used for capacity calculation)
    """
    stats_children = all_children if all_children else present_children
    
    if not stats_children:
        return {
            "total_factor": 0.0,
            "required_educators": 0,
            "calculated_max_capacity": 30,
            "is_compliant": True,
            "has_under_24m": False,
            "has_over_24m": False,
            "errors": []
        }

    # Calculate capacity based on stats_children (all enrolled in this bucket)
    highest_factor = 0.0
    today = date.today()
    for child in stats_children:
        age_months = (today.year - child.birth_date.year) * 12 + today.month - child.birth_date.month
        if today.day < child.birth_date.day: age_months -= 1
        
        factor = 0.0
        if age_months < 24: factor = 0.333
        elif 24 <= age_months < 36: factor = 0.200
        elif 36 <= age_months < 48: factor = 0.125
        elif 48 <= age_months < 60: factor = 0.100
        else: factor = 0.067
        
        if factor > highest_factor: highest_factor = factor

    if highest_factor > 0:
        calculated_max_capacity = int(2.0 / highest_factor)
    else:
        calculated_max_capacity = 30

    # Calculate actual usage based on present_children
    total_educators_factor = 0.0
    has_under_24m = False
    has_over_24m = False
    errors = []

    for child in present_children:
        age_months = (today.year - child.birth_date.year) * 12 + today.month - child.birth_date.month
        if today.day < child.birth_date.day: age_months -= 1

        if age_months < 24: has_under_24m = True
        else: has_over_24m = True

        factor = 0.0
        if age_months < 24: factor = 0.333
        elif 24 <= age_months < 36: factor = 0.200
        elif 36 <= age_months < 48: factor = 0.125
        elif 48 <= age_months < 60: factor = 0.100
        else: factor = 0.067
        
        total_educators_factor += factor

    integer_part = int(total_educators_factor)
    fractional_part = total_educators_factor - integer_part
    
    if fractional_part > 0.05:
        required_educators = integer_part + 1
    else:
        required_educators = integer_part

    is_compliant = not (has_under_24m and has_over_24m)
    if not is_compliant:
        errors.append("Cannot mix children under 24 months with older children.")

    return {
        "total_factor": total_educators_factor,
        "required_educators": required_educators,
        "calculated_max_capacity": calculated_max_capacity,
        "is_compliant": is_compliant,
        "has_under_24m": has_under_24m,
        "has_over_24m": has_over_24m,
        "errors": errors
    }
