from .core.config import CONFIG
from .commands.set_commands import set_default_commands
from .database.db import init_db
from .handlers.__init__ import register_handlers
from .handlers.admin_handler import router
from .utils.scheduler import start_scheduler
