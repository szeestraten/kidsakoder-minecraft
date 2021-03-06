# -*- coding: utf-8 -*-
"""
flask_app.forms
~~~~~~~~~~~~~~~

Flask-WTF form controller
"""

from flask_wtf import Form
from flask_wtf.html5 import EmailField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, DateTimeField, IntegerField, TextAreaField, HiddenField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo


class MeetingForm(Form):
    """ Form for creating meetings """
    title = StringField(u'Tittel', [Length(min=4, max=50)])
    start_time = DateTimeField(u'Starttidspunkt', [InputRequired()], format='%d.%m.%Y %H:%M')
    end_time = DateTimeField(u'Sluttidspunkt', [InputRequired()], format='%d.%m.%Y %H:%M')
    participant_count = IntegerField(u'Antall Minecraft tjenere', [InputRequired()])
    world_id = HiddenField(u'Verden ID')


class WorldForm(Form):
    """ Form for initiating meeting form with world, or to change world description """
    # Insert boolean hidden field to make distinction between forms easier
    is_world_form = HiddenField(u'Er verden', [InputRequired()], default='True')
    world_id = HiddenField(u'Verden ID', [InputRequired()])
    description = TextAreaField(u'Beskrivelse')


class WorldUpload(Form):
    """ Form for uploading Minecraft worlds in zip format """
    description = StringField(u'Navn eller kort beskrivelse', [InputRequired()])
    world_file = FileField(u'Minecraft verden',
                           [FileRequired(), FileAllowed(['zip'], u'Filen må være pakket i zip format')])


class ChangeEmail(Form):
    """ User change email form """
    new_email = EmailField(u'Ny e-post adresse', [Email()])
    confirm_email = EmailField(u'Bekreft e-post adressen',
                               [Email(), EqualTo('new_email', u'E-post adressene er ikke like')])
    # Requires password to change
    password = PasswordField(u'Skriv inn passordet ditt for å bekrefte endringen', [InputRequired()])


class ChangeName(Form):
    """ User change name form """
    new_name = StringField(u'Nytt navn / beskrivelse for denne brukeren', [InputRequired()])


class ChangePassword(Form):
    """ User change password form """
    # TODO password length requirements?
    old_password = PasswordField(u'Gammelt passord', [InputRequired()])
    new_password = PasswordField(u'Nytt passord', [InputRequired()])
    confirm_password = PasswordField(u'Bekreft nytt passord',
                                     [InputRequired(), EqualTo('new_password', u'Passordene er ikke like')])


class ChangePlayername(Form):
    """ User change Minecraft player name for op access to Minecraft servers """
    playername = StringField(u'Ditt minecraft spillernavn', [InputRequired()])
    uuid = StringField(u'Mojang UUID', [InputRequired()])
    # Requires password to change
    password = PasswordField(u'Skriv inn passordet ditt for å bekrefte endringen', [InputRequired()])
