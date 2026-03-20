import functools
import logging

from rest_framework.exceptions import NotFound, ValidationError


logger = logging.getLogger(__name__)


def handle_exceptions(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            msg = str(exc)
            if 'does not exist' in msg:
                raise NotFound(detail=msg) from exc
            raise ValidationError(detail=msg) from exc
        except Exception:
            logger.exception('API error')
            raise

    return wrapper
