"""
Infinit Restaurant - Tenant Isolation Utilities
Enforces multi-tenant data isolation via company field.
"""

import frappe
from frappe import _
import functools


def get_user_company() -> str:
    """Get the company assigned to the current user."""
    if frappe.session.user == "Administrator":
        return None
    
    # Check session cache first
    company = frappe.local.get("user_company")
    if company:
        return company
    
    # Get from user defaults
    company = frappe.defaults.get_user_default("Company")
    if company:
        frappe.local.user_company = company
        return company
    
    # Check custom_company field on user
    company = frappe.db.get_value("User", frappe.session.user, "custom_company")
    if company:
        frappe.local.user_company = company
        return company
    
    return None


def validate_tenant_access(doc, method=None):
    """
    Ensure user can only access their company's data.
    Called on before_insert and validate events.
    """
    # Skip for Administrator
    if frappe.session.user == "Administrator":
        return
    
    # Skip for Guest (will fail permission check anyway)
    if frappe.session.user == "Guest":
        return
    
    # Skip for doctypes without company field
    if not hasattr(doc, "company"):
        return
    
    user_company = get_user_company()
    if not user_company:
        # User has no company assigned, skip check but let Frappe handle permissions
        return
    
    # Auto-set company on new documents
    if doc.is_new() and not doc.company:
        doc.company = user_company
        return
    
    # Validate company matches
    if doc.company and doc.company != user_company:
        frappe.throw(
            _("Access Denied: You can only access data from your own organization."),
            frappe.PermissionError
        )


def apply_tenant_filter(doctype: str, filters: dict = None) -> dict:
    """
    Auto-filter queries by company.
    Use in permission_query_conditions.
    """
    if filters is None:
        filters = {}
    
    if frappe.session.user == "Administrator":
        return filters
    
    user_company = get_user_company()
    if not user_company:
        return filters
    
    # Check if doctype has company field
    meta = frappe.get_meta(doctype)
    if meta.has_field("company"):
        filters["company"] = user_company
    
    return filters


def get_permission_query_conditions(user=None):
    """
    Returns SQL condition for filtering by company.
    Use in permission_query_conditions hook.
    """
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return None
    
    company = frappe.defaults.get_user_default("Company", user=user)
    if not company:
        company = frappe.db.get_value("User", user, "custom_company")
    
    if company:
        return f"(`tabCompany`.`name` = '{company}' OR `company` = '{company}')"
    
    return None


def company_required(func):
    """Decorator to require a company context."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        company = get_user_company()
        if not company:
            frappe.throw(_("Company context required. Please set your default company."))
        return func(*args, **kwargs)
    return wrapper


def is_super_admin() -> bool:
    """Check if current user is a Super Admin."""
    if frappe.session.user == "Administrator":
        return True
    
    return "System Manager" in frappe.get_roles(frappe.session.user)


def is_restaurant_admin() -> bool:
    """Check if current user is a Restaurant Admin."""
    return any(role in frappe.get_roles(frappe.session.user) for role in [
        "Restaurant Admin",
        "Restaurant Manager", 
        "System Manager"
    ])
