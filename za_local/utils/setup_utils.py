"""
Setup Utility Functions

Utility functions used during app setup and installation.
These are separated from setup modules to follow Frappe best practices.
"""


def get_property_type(value):
    """
    Get the property type based on value type for Frappe property setters.
    
    Args:
        value: The value to determine property type for
        
    Returns:
        str: Property type ("Check", "Code", or "Data")
    """
    if isinstance(value, bool) or isinstance(value, int):
        return "Check"
    elif isinstance(value, str):
        if value.startswith("eval:"):
            return "Code"
        return "Data"
    else:
        return "Data"
