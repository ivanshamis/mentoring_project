from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import send_mail

from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    subject: Optional[str]
    body: str


class BaseMessageSender(ABC):
    @abstractmethod
    def send_message(self, user, message: Message):
        pass


class EmailSender(BaseMessageSender):
    sender = settings.DEFAULT_EMAIL_SENDER

    def send_message(self, user, message: Message):
        self._send_email(email=user.email, message=message)

    def _send_email(self, email: str, message: Message):
        send_mail(
            subject=message.subject,
            message=message.body,
            from_email=self.sender,
            recipient_list=[email],
        )


email_sender = EmailSender()
