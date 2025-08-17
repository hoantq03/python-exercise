import re

def is_strong_password(password):
    """
    Checks if a password meets strong criteria:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character from the set @$!%*?&
    """
    pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")

    match_result = pattern.fullmatch(password)

    print(f"Checking password strength for: {password}")
    print(f"Match object: {match_result}")

    return bool(match_result)