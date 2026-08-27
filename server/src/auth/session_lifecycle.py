"""Session expiry helpers for the parent web console."""

from __future__ import annotations

import logging
import os
import time
from enum import Enum

from src.common.oidc import OIDCRefreshError

_LOGGER = logging.getLogger(__name__)

WARN_SECONDS_DEFAULT = 300
OIDC_REFRESH_WINDOW_SECONDS = 60


class OidcRefreshOutcome(str, Enum):
    SKIPPED = 'skipped'
    REFRESHED = 'refreshed'
    TRANSIENT_FAILURE = 'transient_failure'
    AUTH_FAILURE = 'auth_failure'


def session_warn_seconds() -> int:
    raw = os.environ.get('SESSION_WARN_SECONDS')
    if raw is None:
        return WARN_SECONDS_DEFAULT
    try:
        return max(60, int(raw))
    except ValueError:
        return WARN_SECONDS_DEFAULT


def get_oidc_expires_at(session) -> float | None:
    raw = session.get('oidc_token_expires_at')
    if raw is None:
        return None
    return float(raw)


def seconds_until_expiry(session) -> float | None:
    expires_at = get_oidc_expires_at(session)
    if expires_at is None:
        return None
    return expires_at - time.time()


def _refresh_backoff_seconds() -> int:
    return int(os.environ.get('OIDC_REFRESH_BACKOFF_SECONDS', '300'))


def _should_attempt_oidc_refresh(session, *, force: bool) -> bool:
    if not session.get('logged_in') or not session.get('oidc_refresh_token'):
        return False

    refresh_retry_after = session.get('oidc_refresh_retry_after')
    if refresh_retry_after and refresh_retry_after > time.time():
        return False

    if force:
        return True

    expires_at = get_oidc_expires_at(session)
    return expires_at is None or expires_at < time.time() + OIDC_REFRESH_WINDOW_SECONDS


def _apply_refreshed_tokens(session, new_tokens: dict) -> None:
    session['oidc_access_token'] = new_tokens.get('access_token')
    if new_tokens.get('refresh_token'):
        session['oidc_refresh_token'] = new_tokens.get('refresh_token')
    session['oidc_token_expires_at'] = time.time() + new_tokens.get('expires_in', 3600)
    session.pop('oidc_refresh_retry_after', None)
    session.modified = True


def refresh_oidc_session_tokens(session, oidc_helper, *, force: bool = False) -> OidcRefreshOutcome:
    """Refresh OIDC tokens in the current session when needed."""
    if not _should_attempt_oidc_refresh(session, force=force):
        return OidcRefreshOutcome.SKIPPED

    refresh_token = session['oidc_refresh_token']
    try:
        new_tokens = oidc_helper.refresh_access_token(refresh_token)
        _apply_refreshed_tokens(session, new_tokens)
        _LOGGER.info('OIDC access token refreshed successfully.')
        return OidcRefreshOutcome.REFRESHED
    except OIDCRefreshError as exc:
        if exc.is_transient:
            session['oidc_refresh_retry_after'] = time.time() + _refresh_backoff_seconds()
            session.modified = True
            _LOGGER.warning('Transient OIDC refresh failure: %s', exc)
            return OidcRefreshOutcome.TRANSIENT_FAILURE
        if exc.is_expected_auth_failure:
            _LOGGER.info('OIDC refresh token is no longer valid: %s', exc.oauth_error or exc.status_code)
        else:
            _LOGGER.error('Definitive OIDC refresh failure: %s', exc)
        return OidcRefreshOutcome.AUTH_FAILURE
    except Exception as exc:
        session['oidc_refresh_retry_after'] = time.time() + _refresh_backoff_seconds()
        session.modified = True
        _LOGGER.warning('Unexpected error during OIDC token refresh: %s', exc)
        return OidcRefreshOutcome.TRANSIENT_FAILURE


def clear_oidc_session(session) -> None:
    session.pop('oidc_refresh_retry_after', None)
    session.pop('logged_in', None)
    session.pop('user', None)
    session.pop('oidc_access_token', None)
    session.pop('oidc_refresh_token', None)
    session.pop('oidc_token_expires_at', None)
    session.modified = True


def extend_parent_session(session, oidc_helper) -> tuple[bool, str | None]:
    """Extend an authenticated parent session.

    Returns ``(success, api_message_key)`` where the key is relative to ``api.*``.
    """
    if not session.get('logged_in'):
        return False, 'not_authenticated'

    if not session.get('oidc_refresh_token'):
        session.modified = True
        return True, None

    outcome = refresh_oidc_session_tokens(session, oidc_helper, force=True)
    if outcome == OidcRefreshOutcome.REFRESHED:
        _LOGGER.info('Parent session extended via OIDC token refresh.')
        return True, None
    if outcome == OidcRefreshOutcome.TRANSIENT_FAILURE:
        return False, 'session_extend_transient'
    return False, 'session_extend_failed'
