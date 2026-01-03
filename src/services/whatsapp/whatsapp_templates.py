"""
WhatsApp Message Templates
==========================

Defines approved message templates for WhatsApp Business API.
These templates must be pre-registered and approved in Meta Business Suite.

Template Registration: https://business.facebook.com/ → WhatsApp Manager → Message Templates
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TemplateCategory(Enum):
    """WhatsApp template categories"""
    UTILITY = "UTILITY"
    MARKETING = "MARKETING"
    AUTHENTICATION = "AUTHENTICATION"


class TemplateLanguage(Enum):
    """Supported template languages"""
    ENGLISH = "en"
    ENGLISH_US = "en_US"
    ENGLISH_IN = "en_IN"
    HINDI = "hi"


@dataclass
class TemplateVariable:
    """Represents a variable placeholder in a template"""
    index: int  # 1-based index ({{1}}, {{2}}, etc.)
    name: str   # Friendly name for the variable
    example: str  # Example value (required for approval)
    description: str  # Description of what this variable represents


@dataclass
class WhatsAppTemplate:
    """Represents a WhatsApp message template"""
    name: str  # Template name in Meta Business Suite
    category: TemplateCategory
    language: TemplateLanguage
    body_text: str  # Template body with {{1}}, {{2}} placeholders
    variables: List[TemplateVariable]
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    buttons: Optional[List[Dict]] = None
    
    def get_variable_count(self) -> int:
        """Get the number of variables in this template"""
        return len(self.variables)
    
    def format_body(self, values: Dict[str, str]) -> str:
        """
        Format the body text with provided values.
        
        Args:
            values: Dict mapping variable indices ("1", "2") to values
            
        Returns:
            Formatted body text
        """
        formatted = self.body_text
        for var in self.variables:
            placeholder = "{{" + str(var.index) + "}}"
            value = values.get(str(var.index), f"[{var.name}]")
            formatted = formatted.replace(placeholder, value)
        return formatted


# =============================================================================
# PAYMENT LINK TEMPLATE
# =============================================================================
PAYMENT_LINK_TEMPLATE = WhatsAppTemplate(
    name="payment_link_v1",
    category=TemplateCategory.UTILITY,
    language=TemplateLanguage.ENGLISH_IN,
    body_text="""Hello {{1}},

Thank you for your interest in {{2}}.

Your payment amount: ₹{{3}}

Click below to complete your payment securely:
{{4}}

If you have any questions, simply reply to this message.

Thank you for choosing us!""",
    variables=[
        TemplateVariable(
            index=1,
            name="customer_name",
            example="John",
            description="Customer's first name"
        ),
        TemplateVariable(
            index=2,
            name="product_name",
            example="Hotel Booking",
            description="Name of the product/service"
        ),
        TemplateVariable(
            index=3,
            name="amount",
            example="5000",
            description="Payment amount in INR"
        ),
        TemplateVariable(
            index=4,
            name="payment_link",
            example="https://rzp.io/i/abc123",
            description="Razorpay payment link URL"
        )
    ],
    footer_text="SARA AI Assistant"
)


# =============================================================================
# PAYMENT LINK TEMPLATE (HINDI)
# =============================================================================
PAYMENT_LINK_TEMPLATE_HINDI = WhatsAppTemplate(
    name="payment_link_hindi_v1",
    category=TemplateCategory.UTILITY,
    language=TemplateLanguage.HINDI,
    body_text="""नमस्ते {{1}},

{{2}} में आपकी रुचि के लिए धन्यवाद।

आपकी भुगतान राशि: ₹{{3}}

सुरक्षित भुगतान के लिए नीचे क्लिक करें:
{{4}}

कोई सवाल हो तो इस संदेश का जवाब दें।

धन्यवाद!""",
    variables=[
        TemplateVariable(
            index=1,
            name="customer_name",
            example="राहुल",
            description="ग्राहक का नाम"
        ),
        TemplateVariable(
            index=2,
            name="product_name",
            example="होटल बुकिंग",
            description="उत्पाद/सेवा का नाम"
        ),
        TemplateVariable(
            index=3,
            name="amount",
            example="5000",
            description="भुगतान राशि"
        ),
        TemplateVariable(
            index=4,
            name="payment_link",
            example="https://rzp.io/i/abc123",
            description="भुगतान लिंक"
        )
    ],
    footer_text="SARA AI सहायक"
)


# =============================================================================
# CALL FOLLOWUP TEMPLATE
# =============================================================================
CALL_FOLLOWUP_TEMPLATE = WhatsAppTemplate(
    name="call_followup_v1",
    category=TemplateCategory.UTILITY,
    language=TemplateLanguage.ENGLISH_IN,
    body_text="""Hello {{1}},

Thank you for speaking with us today!

Here's a summary of our conversation:
{{2}}

If you have any questions or need further assistance, feel free to reply to this message.

Have a great day!""",
    variables=[
        TemplateVariable(
            index=1,
            name="customer_name",
            example="John",
            description="Customer's first name"
        ),
        TemplateVariable(
            index=2,
            name="call_summary",
            example="We discussed hotel booking options for your Mumbai trip.",
            description="Brief summary of the call"
        )
    ],
    footer_text="SARA AI Assistant"
)


# =============================================================================
# PAYMENT REMINDER TEMPLATE
# =============================================================================
PAYMENT_REMINDER_TEMPLATE = WhatsAppTemplate(
    name="payment_reminder_v1",
    category=TemplateCategory.UTILITY,
    language=TemplateLanguage.ENGLISH_IN,
    body_text="""Hello {{1}},

Just a friendly reminder about your pending payment for {{2}}.

Amount: ₹{{3}}

Complete your payment here: {{4}}

This link will expire soon. If you've already paid, please ignore this message.

Need help? Just reply to this message!""",
    variables=[
        TemplateVariable(
            index=1,
            name="customer_name",
            example="John",
            description="Customer's first name"
        ),
        TemplateVariable(
            index=2,
            name="product_name",
            example="Hotel Booking",
            description="Name of the product/service"
        ),
        TemplateVariable(
            index=3,
            name="amount",
            example="5000",
            description="Payment amount in INR"
        ),
        TemplateVariable(
            index=4,
            name="payment_link",
            example="https://rzp.io/i/abc123",
            description="Razorpay payment link URL"
        )
    ],
    footer_text="SARA AI Assistant"
)


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

# Map of template names to template objects
TEMPLATES: Dict[str, WhatsAppTemplate] = {
    "payment_link": PAYMENT_LINK_TEMPLATE,
    "payment_link_v1": PAYMENT_LINK_TEMPLATE,
    "payment_link_hindi": PAYMENT_LINK_TEMPLATE_HINDI,
    "payment_link_hindi_v1": PAYMENT_LINK_TEMPLATE_HINDI,
    "call_followup": CALL_FOLLOWUP_TEMPLATE,
    "call_followup_v1": CALL_FOLLOWUP_TEMPLATE,
    "payment_reminder": PAYMENT_REMINDER_TEMPLATE,
    "payment_reminder_v1": PAYMENT_REMINDER_TEMPLATE,
}


def get_template(name: str) -> Optional[WhatsAppTemplate]:
    """
    Get a template by name.
    
    Args:
        name: Template name (e.g., "payment_link" or "payment_link_v1")
        
    Returns:
        WhatsAppTemplate object or None if not found
    """
    return TEMPLATES.get(name)


def get_template_for_language(base_name: str, language: str) -> Optional[WhatsAppTemplate]:
    """
    Get a template for a specific language.
    
    Args:
        base_name: Base template name (e.g., "payment_link")
        language: Language code ("en", "hi", etc.)
        
    Returns:
        WhatsAppTemplate object or None if not found
    """
    if language in ["hi", "hindi"]:
        hindi_template = TEMPLATES.get(f"{base_name}_hindi")
        if hindi_template:
            return hindi_template
    
    return TEMPLATES.get(base_name)


def list_templates() -> List[str]:
    """Get list of available template names"""
    # Return unique template names (without version suffixes)
    unique_names = set()
    for name in TEMPLATES.keys():
        if not name.endswith("_v1"):
            unique_names.add(name)
    return sorted(unique_names)


def validate_template_variables(
    template_name: str,
    variables: Dict[str, str]
) -> tuple[bool, Optional[str]]:
    """
    Validate that all required variables are provided for a template.
    
    Args:
        template_name: Template name
        variables: Dict of variable values
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    template = get_template(template_name)
    if not template:
        return False, f"Template '{template_name}' not found"
    
    missing = []
    for var in template.variables:
        if str(var.index) not in variables:
            missing.append(var.name)
    
    if missing:
        return False, f"Missing required variables: {', '.join(missing)}"
    
    return True, None

