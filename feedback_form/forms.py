"""Forms for the ``feedback_form`` app."""
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse

from django.core.mail import EmailMultiAlternatives
from django.template.context import Context
from django.template.loader import get_template

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """
    A feedback form with modern spam protection.

    :url: Field to trap spam bots.

    """
    url = forms.URLField(required=False)

    def __init__(self, user=None, url=None, prefix='feedback',
                 content_object=None, *args, **kwargs):
        self.content_object = content_object
        self.request = kwargs.pop('request', None)
        super(FeedbackForm, self).__init__(prefix='feedback', *args, **kwargs)
        if url:
            self.instance.current_url = url
        if user:
            self.instance.user = user
            del self.fields['email']
        else:
            self.fields['email'].required = True

    def save(self):
        if not self.cleaned_data.get('url'):
            self.instance.content_object = self.content_object
            obj = super(FeedbackForm, self).save()
            feedback_url = reverse('admin:feedback_form_feedback_change',
                               args=(obj.id, ))
            if self.request:
                feedback_url = self.request.build_absolute_uri(feedback_url)
            context = {
                'feedback_url': feedback_url,
                'feedback': obj,
            }
            subject = get_template('feedback_form/email/subject.html').render(
                Context(context)
            )
            message_body = get_template('feedback_form/email/body.html').render(
                Context(context)
            )
            msg = EmailMultiAlternatives(
                subject,
                message_body,
                from_email=settings.FROM_EMAIL,
                to=[manager[1] for manager in settings.MANAGERS],
            )
            msg.attach_alternative(message_body, "text/html")
            msg.send()
            if getattr(settings, 'FEEDBACK_EMAIL_CONFIRMATION', False):
                email = None
                if obj.email:
                    email = obj.email
                elif obj.user.email:
                    email = obj.user.email
                if email:
                    subject = get_template('feedback_form/email/confirmation_subject.html').render(
                        Context(context)
                    )
                    message_body = get_template('feedback_form/email/confirmation_body.html').render(
                        Context(context)
                    )
                    msg = EmailMultiAlternatives(
                        subject,
                        message_body,
                        from_email=settings.FROM_EMAIL,
                        to=[email],
                    )
                    msg.attach_alternative(message_body, "text/html")
                    msg.send()
            return obj

    class Media:
        css = {'all': ('feedback_form/css/feedback_form.css'), }
        js = ('feedback_form/js/feedback_form.js', )

    class Meta:
        model = Feedback
        fields = ('email', 'message')
