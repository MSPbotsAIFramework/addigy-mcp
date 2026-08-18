from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured", "No Addigy API key. Send the X-Addigy-Api-Key header.", False
)
