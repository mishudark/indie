from django import forms
from mongoforms.fields import *
from django.forms.widgets import Textarea, TextInput
from django.forms.fields import *

class ListField(mongoengine.fields.ListField):
    def clean(self, value):
        return self.validate(value)

class MongoFormFieldGeneratorCustom(MongoFormFieldGenerator):
    def generate_localstorageimagefield(self, field_name, field, label):
        return forms.ImageField(
                label=label,
                required=field.required
                )

    def generate_localstoragefield(self, field_name, field, label):
        return forms.FileField(
                label=label,
                required=field.required
                )

    def generate_listfield(self, field_name, field, label):
        return ListField(field.field)
