import logging
import concurrent.futures
import time
from validate_email import validate_email
import dns.resolver
import smtplib
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use multiple DNS servers for faster lookups
dns_servers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']  # Google, Cloudflare, Quad9
dns.resolver.default_resolver = dns.resolver.Resolver()
dns.resolver.default_resolver.nameservers = dns_servers
dns.resolver.default_resolver.cache = dns.resolver.Cache()  # Enable DNS caching

def check_mx_record(domain):
    """Check MX records with reduced timeout."""
    try:
        dns.resolver.timeout = 5  # Reduced timeout
        dns.resolver.lifetime = 5
        mx_records = dns.resolver.resolve(domain, 'MX')
        return {"status": "Success", "message": "MX records found", "mx_records": mx_records}
    except dns.resolver.Timeout:
        return {"status": "Timeout", "message": "DNS lookup timed out"}
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {"status": "Failed", "message": "No MX records found"}
    except Exception as e:
        return {"status": "Error", "message": f"DNS error: {e}"}

def check_smtp(email, mx_records):
    """Perform SMTP validation with reduced timeout."""
    try:
        if not mx_records:
            return {"status": "Failed", "message": "No valid mail servers found"}

        mx_record = sorted(mx_records, key=lambda x: x.preference)[0]
        mx_domain = str(mx_record.exchange).rstrip('.')

        # Perform SMTP validation (Full check, no skipping)
        is_valid = validate_email(
            email_address=email,
            check_format=True,
            check_blacklist=True,
            check_dns=True,
            dns_timeout=5,  # Reduced timeout
            check_smtp=True,
            smtp_timeout=5,  # Reduced timeout
            smtp_helo_host=socket.gethostname(),
            smtp_from_address='verify@example.com',
            smtp_debug=False
        )

        return {"status": "Success" if is_valid else "Failed",
                "message": "Email is active" if is_valid else "Email does not exist"}

    except smtplib.SMTPException as e:
        return {"status": "Error", "message": f"SMTP error: {e}"}
    except Exception as e:
        return {"status": "Error", "message": f"Validation error: {e}"}

def validate_email_address(email: str) -> dict:
    """Parallelized email validation with DNS caching & reduced timeouts."""
    start_time = time.time()

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

    end_time = time.time()
    results["time_taken"] = round(end_time - start_time, 2)  # Track execution time
    return results
