"""
LDAP Authentication Module
Handles user authentication against LDAP server based on user's configuration.
"""
import os
import ldap3
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LDAPAuthenticator:
    """
    LDAP authentication handler.
    Based on the configuration from user's LDAP setup.
    """

    def __init__(
        self,
        ldap_server: Optional[str] = None,
        ldap_base_dn: Optional[str] = None,
        use_ssl: Optional[bool] = None
    ):
        """
        Initialize LDAP authenticator.

        Args:
            ldap_server: LDAP server URL (e.g., 'ldap://...' or 'ldaps://...')
            ldap_base_dn: Base DN for users (e.g., 'ou=Users,ou=global,dc=analog,dc=com')
            use_ssl: Whether to use SSL/TLS (auto-detected from URL if not specified)
        """
        self.ldap_server = ldap_server or os.environ.get(
            "LDAP_SERVER",
            "ldap://adblrhldap.adbldesign.analog.com"
        )
        self.ldap_base_dn = ldap_base_dn or os.environ.get(
            "LDAP_BASE_DN",
            "ou=Users,ou=global,dc=analog,dc=com"
        )

        # Auto-detect SSL from URL scheme if not explicitly set
        if use_ssl is None:
            self.use_ssl = self.ldap_server.startswith("ldaps://")
        else:
            self.use_ssl = use_ssl

        ssl_status = "with SSL" if self.use_ssl else "without SSL"
        logger.info(f"LDAP Authenticator initialized: {self.ldap_server} ({ssl_status})")

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate user against LDAP server.

        Args:
            username: Username (e.g., 'prajendr')
            password: User password

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not username or not password:
            return False, "Username and password are required"

        try:
            # Create server object
            server = ldap3.Server(
                self.ldap_server,
                use_ssl=self.use_ssl,
                get_info=ldap3.ALL
            )

            # Construct user DN
            user_dn = f"uid={username},{self.ldap_base_dn}"

            logger.info(f"Attempting LDAP authentication for user: {username}")
            logger.debug(f"User DN: {user_dn}")

            # Attempt to bind with user credentials
            conn = ldap3.Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=False
            )

            # Try to bind
            if conn.bind():
                logger.info(f"Authentication successful for user: {username}")
                conn.unbind()
                return True, None
            else:
                logger.warning(f"Authentication failed for user: {username}")
                return False, "Invalid credentials"

        except ldap3.core.exceptions.LDAPBindError as e:
            logger.error(f"LDAP bind error for user {username}: {e}")
            return False, "Invalid credentials"

        except ldap3.core.exceptions.LDAPSocketOpenError as e:
            logger.error(f"LDAP connection error: {e}")
            return False, "Unable to connect to LDAP server"

        except ldap3.core.exceptions.LDAPException as e:
            logger.error(f"LDAP error during authentication: {e}")
            return False, f"Authentication error: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return False, "Authentication system error"

    def get_user_info(self, username: str, password: str) -> Optional[dict]:
        """
        Get user information from LDAP after successful authentication.

        Args:
            username: Username
            password: Password

        Returns:
            Dictionary with user info or None if authentication fails
        """
        success, error = self.authenticate(username, password)

        if not success:
            return None

        try:
            # Create server and connection
            server = ldap3.Server(self.ldap_server, use_ssl=self.use_ssl, get_info=ldap3.ALL)
            user_dn = f"uid={username},{self.ldap_base_dn}"

            conn = ldap3.Connection(server, user=user_dn, password=password)

            if not conn.bind():
                return None

            # Search for user attributes
            conn.search(
                search_base=self.ldap_base_dn,
                search_filter=f"(uid={username})",
                attributes=['cn', 'mail', 'displayName', 'ou', 'memberOf']
            )

            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    'username': username,
                    'cn': str(entry.cn) if hasattr(entry, 'cn') else username,
                    'email': str(entry.mail) if hasattr(entry, 'mail') else None,
                    'display_name': str(entry.displayName) if hasattr(entry, 'displayName') else username,
                    'groups': [str(g) for g in entry.memberOf] if hasattr(entry, 'memberOf') else []
                }

                conn.unbind()
                return user_info

            conn.unbind()
            return None

        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return None


# Singleton instance
_ldap_authenticator = None


def get_ldap_authenticator() -> LDAPAuthenticator:
    """Get or create LDAP authenticator instance."""
    global _ldap_authenticator
    if _ldap_authenticator is None:
        _ldap_authenticator = LDAPAuthenticator()
    return _ldap_authenticator
