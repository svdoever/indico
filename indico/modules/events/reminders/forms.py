# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from datetime import datetime, date

import pytz
from babel.dates import get_timezone
from flask import session
from wtforms.ext.dateutil.fields import DateField
from wtforms.fields import BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from wtforms_components import TimeField

from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import EmailListField, IndicoRadioField, TimeDeltaField
from indico.web.forms.validators import UsedIf
from MaKaC.common.timezoneUtils import DisplayTZ


class ReminderForm(IndicoForm):
    default_widget_attrs = {'absolute_time': {'placeholder': 'HH:MM'}}
    recipient_fields = {'recipients', 'send_to_participants'}
    schedule_fields = {'schedule_type', 'absolute_date', 'absolute_time', 'relative_delta'}
    schedule_recipient_fields = recipient_fields | schedule_fields

    # Schedule
    schedule_type = IndicoRadioField(_('Type'), [DataRequired()],
                                     choices=[('relative', _("Relative to the event start time")),
                                              ('absolute', _("Fixed date/time")),
                                              ('now', _('Send immediately'))])
    relative_delta = TimeDeltaField(_('Offset'), [UsedIf(lambda form, field: form.schedule_type.data == 'relative'),
                                                  DataRequired()])
    absolute_date = DateField(_('Date'), [UsedIf(lambda form, field: form.schedule_type.data == 'absolute'),
                                          DataRequired()], parse_kwargs={'dayfirst': True})
    absolute_time = TimeField(_('Time'), [UsedIf(lambda form, field: form.schedule_type.data == 'absolute'),
                                          InputRequired()])
    # Recipients
    recipients = EmailListField(_('Email addresses'), description=_('One email address per line.'))
    send_to_participants = BooleanField(_('Participants'),
                                        description=_('Send the reminder to all participants/registrants '
                                                      'of the event.'))
    # Misc
    reply_to_address = SelectField(_('Sender'), [DataRequired()],
                                   description=_('The email address that will show up as the sender.'))
    message = TextAreaField(_('Note'), description=_('A custom message to include in the email.'))
    include_summary = BooleanField(_('Include agenda'),
                                   description=_("Includes a simple text version of the event's agenda in the email."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(ReminderForm, self).__init__(*args, **kwargs)
        self.absolute_time.description = _('Your active timezone is {tz}.').format(tz=self.timezone)
        self._set_email_choices()
        if self.event.getType() == 'simple_event':
            del self.include_summary

    def _set_email_choices(self):
        # User
        emails = {session.user.email: session.user.full_name}
        # Creator
        emails[self.event.getCreator().getEmail()] = self.event.getCreator().getStraightFullName(upper=False)
        # Support
        support = self.event.getSupportInfo()
        emails[support.getEmail()] = support.getCaption() or support.getEmail()
        # Chairs
        emails.update((x.getEmail(), x.getDirectFullName()) for x in self.event.getChairList())
        # Current email to avoid destructive modifications
        emails.setdefault(self.reply_to_address.object_data, self.reply_to_address.object_data)
        # Sanitize and format emails
        emails = {to_unicode(email.strip().lower()): '{} <{}>'.format(name, email)
                  for email, name in emails.iteritems()
                  if email and email.strip()}
        self.reply_to_address.choices = sorted(emails.items(), key=lambda x: (x[0] != session.user.email, x[1].lower()))

    def validate_recipients(self, field):
        if not field.data and not self.send_to_participants.data:
            raise ValidationError(_('If participants are not included you need to specify recipients.'))

    def validate_send_to_participants(self, field):
        if not field.data and not self.recipients.data:
            raise ValidationError(_('If no recipients are specified you need to include participants.'))

    def validate_schedule_type(self, field):
        # Be graceful and allow a reminder that's in the past but on the same day.
        # It will be sent immediately but that way we are a little bit more user-friendly
        if field.data != 'now' and self.scheduled_dt.data.date() < now_utc().date():
            raise ValidationError(_('The specified date is in the past'))

    def validate_absolute_date(self, field):
        if self.schedule_type.data == 'absolute' and field.data < date.today():
            raise ValidationError(_('The specified date is in the past'))

    @property
    def timezone(self):
        return DisplayTZ(conf=self.event).getDisplayTZ()

    @generated_data
    def scheduled_dt(self):
        if self.schedule_type.data == 'absolute':
            dt = datetime.combine(self.absolute_date.data, self.absolute_time.data)
            return get_timezone(self.timezone).localize(dt).astimezone(pytz.utc)
        elif self.schedule_type.data == 'relative':
            return self.event.getStartDate() - self.relative_delta.data
        elif self.schedule_type.data == 'now':
            return now_utc()

    @generated_data
    def event_start_delta(self):
        return self.relative_delta.data if self.schedule_type.data == 'relative' else None
