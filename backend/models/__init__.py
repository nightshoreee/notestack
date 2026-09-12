"""Import every model here so a single `from models import X` works anywhere,
and so Base.metadata.create_all() in main.py sees all tables at once."""
from .user import User
from .course import Course
from .lecture import Lecture
from .segment import Segment
from .node import Node
from .progress import Progress
from .confusion_flag import ConfusionFlag
