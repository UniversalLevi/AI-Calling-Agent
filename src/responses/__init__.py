"""
Response Module
===============

Main module for the responses package.
"""

from .response_factory import ResponseFactory, get_response_factory, generate_response, get_greeting
from .legacy_response import LegacyResponseHandler
from .humanized_response import HumanizedResponseHandler

__all__ = [
    'ResponseFactory',
    'LegacyResponseHandler', 
    'HumanizedResponseHandler',
    'get_response_factory',
    'generate_response',
    'get_greeting'
]


