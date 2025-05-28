"""
Authentication middleware for Streamlit applications.

This module provides decorators and context managers for handling authentication
in a centralized way, following the middleware pattern.
"""

import functools
from typing import Optional, Callable, Any, Dict
import streamlit as st
from auth import validate_jwt, can_modify_entry


class AuthContext:
    """Authentication context that holds current user information."""
    
    def __init__(self):
        self.jwt_token: Optional[str] = None
        self.user_payload: Optional[Dict[str, Any]] = None
        self.is_authenticated: bool = False
        self.username: Optional[str] = None
    
    @classmethod
    def from_session_state(cls) -> 'AuthContext':
        """Create AuthContext from current Streamlit session state."""
        context = cls()
        context.jwt_token = st.session_state.get('jwt')
        
        if context.jwt_token:
            context.user_payload = validate_jwt(context.jwt_token)
            if context.user_payload:
                context.is_authenticated = True
                context.username = context.user_payload.get('sub', '')
        
        return context
    
    def can_modify_entry(self, entry_name: str) -> bool:
        """Check if current user can modify the given entry."""
        if not self.is_authenticated or not entry_name:
            return False
        return can_modify_entry(self.jwt_token, entry_name)


def require_auth(message: str = "Please log in to access this feature"):
    """
    Decorator that requires authentication to access a function.
    
    Args:
        message: Custom message to show when authentication is required
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            auth_context = AuthContext.from_session_state()
            
            if not auth_context.is_authenticated:
                st.warning(f"🔒 {message}")
                return None
            
            # Inject auth_context as first argument
            return func(auth_context, *args, **kwargs)
        
        return wrapper
    return decorator


def with_auth_context(func: Callable) -> Callable:
    """
    Decorator that injects auth context into a function without requiring authentication.
    Useful for functions that need to behave differently based on auth state.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        auth_context = AuthContext.from_session_state()
        # Inject auth_context as first argument
        return func(auth_context, *args, **kwargs)
    
    return wrapper


def auth_button(
    auth_context: AuthContext,
    label: str,
    unauthorized_label: str = None,
    entry_name: str = None,
    require_entry_ownership: bool = False,
    **button_kwargs
) -> bool:
    """
    Create a button that respects authentication state and entry ownership.
    
    Args:
        auth_context: Current authentication context
        label: Button label when authorized
        unauthorized_label: Button label when unauthorized
        entry_name: Name of entry for ownership check
        require_entry_ownership: Whether to check entry ownership
        **button_kwargs: Additional arguments passed to st.button
    
    Returns:
        True if button was clicked and user is authorized, False otherwise
    """
    # If entry ownership is required but no entry name provided, disable the button
    if require_entry_ownership and not entry_name:
        button_kwargs.update({
            'disabled': True,
            'help': "Select a row to access this feature"
        })
        return st.button(label, **button_kwargs)
    
    if not auth_context.is_authenticated:
        if unauthorized_label is None:
            # Extract action from label (remove emoji and clean up)
            action = label.replace("✏️", "").replace("🗑️", "").strip()
            unauthorized_label = f"🔒 Log in to {action}"
        button_kwargs.update({
            'disabled': True,
            'help': "Please log in to access this feature"
        })
        return st.button(unauthorized_label, **button_kwargs)
    
    if require_entry_ownership and entry_name:
        if not auth_context.can_modify_entry(entry_name):
            if unauthorized_label is None:
                # Extract action from label (remove emoji and clean up)  
                action = label.replace("✏️", "").replace("🗑️", "").strip()
                unauthorized_label = f"🚫 {action}"
            button_kwargs.update({
                'disabled': True,
                'help': "You can only modify your own entries"
            })
            return st.button(unauthorized_label, **button_kwargs)
    
    return st.button(label, **button_kwargs)


class AuthGuard:
    """Context manager for authentication-protected sections."""
    
    def __init__(self, 
                 message: str = "Please log in to access this feature",
                 require_entry_ownership: bool = False,
                 entry_name: str = None):
        self.message = message
        self.require_entry_ownership = require_entry_ownership
        self.entry_name = entry_name
        self.auth_context = None
        self.authorized = False
    
    def __enter__(self) -> AuthContext:
        self.auth_context = AuthContext.from_session_state()
        
        if not self.auth_context.is_authenticated:
            st.warning(f"🔒 {self.message}")
            self.authorized = False
            return self.auth_context
        
        if self.require_entry_ownership and self.entry_name:
            if not self.auth_context.can_modify_entry(self.entry_name):
                st.warning("🔒 You can only modify your own entries")
                self.authorized = False
                return self.auth_context
        
        self.authorized = True
        return self.auth_context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @property
    def is_authorized(self) -> bool:
        """Check if the current context is authorized."""
        return self.authorized


def get_auth_status() -> Dict[str, Any]:
    """
    Get current authentication status for display purposes.
    
    Returns:
        Dictionary with authentication status information
    """
    auth_context = AuthContext.from_session_state()
    return {
        'is_authenticated': auth_context.is_authenticated,
        'username': auth_context.username,
        'jwt_token': bool(auth_context.jwt_token)
    }
