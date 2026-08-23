"""
The one exception type every AI-layer caller catches, regardless of which
provider is active. Lives in its own file, separate from client.py, so
both the provider modules and the facade can import it without a
circular dependency (client.py imports the providers; the providers need
this exception too).
"""


class AIProviderError(Exception):
    """Raised when an AI provider call fails, wrapping the underlying cause."""
