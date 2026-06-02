import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "secret_key",
    [
        "change_this_secret",
        "super-secret-key",
        "replace_with_random_secret_at_least_32_chars",
        "short-secret",
    ],
)
def test_rejects_insecure_secret_keys(secret_key: str):
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY=secret_key, _env_file=None)


def test_accepts_random_length_secret_key():
    secret_key = "p3L0sS5jHbeZzK44B_4dQk0Q-hkO3tD8MxV1YpR7"

    configured = Settings(SECRET_KEY=secret_key, _env_file=None)

    assert configured.SECRET_KEY == secret_key


@pytest.mark.parametrize("password", ["admin123", "replace_with_strong_initial_admin_password", "small"])
def test_rejects_weak_initial_admin_password(password: str):
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="p3L0sS5jHbeZzK44B_4dQk0Q-hkO3tD8MxV1YpR7",
            INITIAL_ADMIN_PASSWORD=password,
            _env_file=None,
        )
