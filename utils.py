from validate_email import validate_email
import dns.resolver
import smtplib
from email.utils import parseaddr
import socket

def validate_email_address(email: str) -> tuple[bool, str]:
    """
    Validates an email address by checking format and attempting SMTP verification
    Returns a tuple of (is_valid, message)
    """
    try:
        # Basic format check
        if not email or '@' not in email:
            return False, "Invalid email format"

        _, domain = email.split('@')

        # Check domain length
        if len(domain) > 255:
            return False, "Domain name is too long"

        # Verify domain has MX record
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                return False, "Domain doesn't have a valid mail server"

            # Get the MX server with highest priority
            mx_record = sorted(mx_records, key=lambda x: x.preference)[0]
            mx_domain = str(mx_record.exchange).rstrip('.')

            # Attempt SMTP verification
            is_valid = validate_email(
                email_address=email,
                check_format=True,
                check_blacklist=True,
                check_dns=True,
                dns_timeout=10,
                check_smtp=True,
                smtp_timeout=10,
                smtp_helo_host=socket.gethostname(),
                smtp_from_address='verify@example.com',
                smtp_debug=False
            )

            if not is_valid:
                return False, "Email address does not exist or cannot receive emails"

            return True, "Email address is valid and deliverable!"

        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            return False, "Domain does not have mail servers configured"
        except socket.timeout:
            return False, "Connection timed out while verifying email"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"

    except Exception as e:
        return False, f"Validation error: {str(e)}"
