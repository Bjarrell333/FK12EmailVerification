import logging
import concurrent.futures
from validate_email import validate_email
import dns.resolver
import smtplib
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use Google's Public DNS for better reliability & enable DNS caching
dns.resolver.default_resolver = dns.resolver.Resolver()
dns.resolver.default_resolver.nameservers = ['8.8.8.8']  # Google's Public DNS
dns.resolver.default_resolver.cache = dns.resolver.Cache()  # Enable DNS caching

def check_mx_record(domain):
    """Checks if the domain has a valid MX record (Runs in Parallel)."""
    try:
        dns.resolver.timeout = 10  # Lower timeout for speed
        dns.resolver.lifetime = 10

        mx_records = dns.resolver.resolve(domain, 'MX')
        return {"status": "Success", "message": "MX records found", "mx_records": mx_records}
    except dns.resolver.Timeout:
        logging.error(f"DNS Timeout: MX lookup for {domain} took too long.")
        return {"status": "Timeout", "message": "MX lookup timed out"}
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        logging.error(f"DNS Error: No MX records found for {domain}")
        return {"status": "Failed", "message": "No MX records found"}
    except Exception as e:
        logging.error(f"DNS Check Failed: {e}")
        return {"status": "Error", "message": f"DNS error: {e}"}

def check_smtp(email, mx_records):
    """Performs SMTP validation (Runs in Parallel)."""
    try:
        if not mx_records:
            return {"status": "Failed", "message": "No valid mail servers found"}

        mx_record = sorted(mx_records, key=lambda x: x.preference)[0]
        mx_domain = str(mx_record.exchange).rstrip('.')

        logging.info(f"Using MX server: {mx_domain}")

        # Perform SMTP validation (Actual mailbox check)
        is_valid = validate_email(
            email_address=email,
            check_format=True,
            check_blacklist=True,
            check_dns=True,
            dns_timeout=10,  # Lower timeout for speed
            check_smtp=True,
            smtp_timeout=10,  # Lower SMTP timeout
            smtp_helo_host=socket.gethostname(),
            smtp_from_address='verify@example.com',
            smtp_debug=False
        )

        return {"status": "Success" if is_valid else "Failed",
                "message": "Email is valid" if is_valid else "Email does not exist"}

    except smtplib.SMTPException as e:
        logging.error(f"SMTP Check Failed: {e}")
        return {"status": "Error", "message": f"SMTP error: {e}"}
    except Exception as e:
        logging.error(f"Unexpected SMTP Error: {e}")
        return {"status": "Error", "message": f"Validation error: {e}"}

def validate_email_address(email: str) -> dict:
    """Parallelized email validation with DNS caching & timeout handling."""
    try:
        logging.info(f"Validating email: {email}")

        results = {
            "email": email,
            "format": {"status": "Success", "message": "Valid email format"},
            "dns": {"status": "Pending", "message": "Checking MX records..."},
            "smtp": {"status": "Pending", "message": "Verifying SMTP connection..."},
        }

        # Basic format check
        if not email or '@' not in email:
            results["format"] = {"status": "Failed", "message": "Invalid email format"}
            return results

        _, domain = email.split('@')

        # Check domain length
        if len(domain) > 255:
            results["format"] = {"status": "Failed", "message": "Domain name is too long"}
            return results

        # Run MX lookup & SMTP check in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_mx = executor.submit(check_mx_record, domain)
            mx_result = future_mx.result()
            results["dns"] = mx_result

            if mx_result["status"] == "Success":
                mx_records = mx_result["mx_records"]
                future_smtp = executor.submit(check_smtp, email, mx_records)
                smtp_result = future_smtp.result()
                results["smtp"] = smtp_result

        return results

    except Exception as e:
        logging.error(f"Validation error: {e}")
        return {"status": "Error", "message": f"Validation error: {e}"}
