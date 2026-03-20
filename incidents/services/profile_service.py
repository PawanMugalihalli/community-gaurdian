import logging
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

VALID_CONCERNS = {'physical', 'digital', 'weather'}


class UserProfileService:

    @staticmethod
    def create(data: dict) -> User:
        concerns = data.get('concerns', [])
        UserProfileService._validate_concerns(concerns)
        return User.objects.create(**data)

    @staticmethod
    def get_by_id(user_id: int) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User with id {user_id} does not exist.")

    @staticmethod
    def update(user_id: int, data: dict) -> User:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User with id {user_id} does not exist.")

        if 'concerns' in data:
            UserProfileService._validate_concerns(data['concerns'])

        allowed_fields = {'name', 'location', 'concerns'}
        for field, value in data.items():
            if field in allowed_fields:
                setattr(user, field, value)

        user.save()
        return user

    @staticmethod
    def _validate_concerns(concerns: list) -> None:
        invalid = set(concerns) - VALID_CONCERNS
        if invalid:
            raise ValueError(
                f"Invalid concern types: {invalid}. "
                f"Must be one of {VALID_CONCERNS}"
            )