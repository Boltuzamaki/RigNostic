import os

from . import create_app

create_app().run(
    host=os.getenv("RIGNOSTIC_HOST", "127.0.0.1"),
    port=int(os.getenv("RIGNOSTIC_PORT", "5000")),
    debug=os.getenv("RIGNOSTIC_DEBUG", "1") == "1",
)
