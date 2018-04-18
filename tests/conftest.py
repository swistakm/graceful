import warnings

# these fixtures will be available for whole tests package
from .fixtures import *  # noqa


# supress all future warnings for better log output
warnings.simplefilter("ignore", FutureWarning)
