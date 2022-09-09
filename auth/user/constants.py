from user.message_sender import Message

MIN_PASSWORD_LENGTH = 8


class ErrorMessages:
    # LoginSerializer
    USER_IS_DEACTIVATED = "This user has been deactivated."
    USER_WRONG_CREDENTIALS = "A user with this email and password was not found."

    # UserManager
    USER_MUST_HAVE_USERNAME = "Users must have a username."
    USER_MUST_HAVE_EMAIL = "Users must have an email address."
    SUPERUSER_MUST_HAVE_PASSWORD = "Superusers must have a password."

    NOT_AUTHENTICATED = "Authentication credentials were not provided."
    NOT_FOUND = "Not found."
    NOT_ALLOWED = "Not allowed"
    FIELD_IS_REQUIRED = "This field is required."
    NOT_VALID_EMAIL = "Enter a valid email address."
    NO_PERMISSION = "You do not have permission to perform this action."

    USER_FIELD_EXISTS = "user with this {field} already exists."
    WEAK_PASSWORD = "Ensure this field has at least {min_length} characters."
    WEAK_PASSWORD_SPEC = "Ensure the password contains characters in both cases, digits and special characters"
    INVALID_TOKEN = "Invalid token"
    INVALID_TOKEN_ACTION = "Invalid token action"
    INVALID_TOKEN_USER = "The user corresponding to the given token was not found."
    USER_NOT_FOUND = "User not found"

    PASSWORD_NO_MATCH = "The passwords don't match"
    PASSWORD_IS_WRONG = "The old password is wrong"
    PASSWORD_THE_SAME = "The new password must be different from the old one"


class EmailTemplates:
    templates = {
        "ACTIVATE_ACCOUNT": Message(
            subject="Please activate your account",
            body="Activation URL: {url}",
        ),
        "PASSWORD_RESET": Message(
            subject="Password reset",
            body="Password reset url: {url}",
        ),
        "PASSWORD_SETUP": Message(
            subject="Password setup",
            body="Password setup url: {url}",
        ),
    }


email_templates = EmailTemplates()
