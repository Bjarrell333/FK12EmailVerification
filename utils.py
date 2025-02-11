import logging
from validate_email import validate_email
import dns.resolver
import smtplib
import socket

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)

# Use Google's Public DNS to avoid Render's internal DNS resolver issues
dns.resolver.default_resolver = dns.resolver.Resolver()
dns.resolver.default_resolver.nameservers = ['8.8.8.8']  # Google's Public DNS

def validate_email_address(email: str) -> tuple[bool, str]:
    """
    Validates an email address by checking format and attempting SMTP verification.
    Returns a tuple of (is_valid, message).
    """
    try:
        logging.info(f"Validating email: {email}")

        # Basic format check
        if not email or '@' not in email:
            logging.error("Invalid email format")
            return False, "Invalid email format"

        _, domain = email.split('@')

        # Check domain length
        if len(domain) > 255:
            logging.error("Domain name is too long")
            return False, "Domain name is too long"

        # Verify domain has MX record
        try:
            logging.info(f"Resolving MX records for {domain} with increased timeout")
            
            # Increase timeout for DNS resolution
            dns.resolver.timeout = 15
            dns.resolver.lifetime = 15

            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                logging.error("Domain doesn't have a valid mail server")
                return False, "Domain doesn't have a valid mail server"

            # Get the MX server with the highest priority
            mx_record = sorted(mx_records, key=lambda x: x.preference)[0]
            mx_domain = str(mx_record.exchange).rstrip('.')

            logging.info(f"Using MX server: {mx_domain}")

            # Attempt SMTP verification with increased timeout
            is_valid = validate_email(
                email_address=email,
                check_format=True,
                check_blacklist=True,
                check_dns=True,
                dns_timeout=15,  # Increased timeout for DNS resolution
                check_smtp=True,  # Keep this True for SMTP validation
                smtp_timeout=15,   #  Increased SMTP timeout
                smtp_helo_host=socket.gethostname(),
                smtp_from_address='verify@example.com',
                smtp_debug=False
            )

            if not is_valid:
                logging.error("Email address does not exist or cannot receive emails")
                return False, "Email address does not exist or cannot receive emails"

            logging.info("Email validation successful!")
            return True, "Email address is valid and deliverable!"

        except dns.resolver.NXDOMAIN:
            logging.error("Domain does not exist")
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            logging.error("Domain does not have mail servers configured")
            return False, "Domain does not have mail servers configured"
        except socket.timeout:
            logging.error("Connection timed out while verifying email")
            return False, "Connection timed out while verifying email"
        except smtplib.SMTPException as e:
            logging.error(f"SMTP error: {str(e)}")
            return False, f"SMTP error: {str(e)}"

    except Exception as e:
        logging.error(f"Validation error: {str(e)}")
        return False, f"Validation error: {str(e)}"
