from django import forms
from django.core.validators import EMPTY_VALUES, RegexValidator
from django.utils.encoding import smart_unicode
from django.db.models.options import get_verbose_name
from django.utils.text import capfirst

from mongoengine import ReferenceField as MongoReferenceField
from mongoengine.fields import StringField

from fields import MongoCharField, ReferenceField, DocumentMultipleChoiceField, DictField

BLANK_CHOICE_DASH = [("", "---------")]

class ListField(forms.Field):
    """
    List field for mongo forms.
    Uses MultiValueField from django.forms module.
    """
    field_name_separator = '__'

    def __init__(self, field, field_name_base, list_size=2, *args, **kwargs):
        forms.Field.__init__(self, *args, **kwargs)
        self.fields = []
        self.field_name_base = field_name_base

        field_generator = MongoFormFieldGenerator()

        for field_num in range(list_size):
            field_name = '%s%s%s' % (field_name_base,
                                    self.field_name_separator, field_num)

            self.fields.append(field_generator.generate(field, field_name))
    def clean(self, value):
        items = []
        for val in value:
            items.append(self.fields[0].clean(val))
        return items

class MongoFormFieldGenerator(object):
    """This class generates Django form-fields for mongoengine-fields."""

    def generate(self, field, charfield_default=False, **kwargs):
        """Tries to lookup a matching formfield generator (lowercase
        field-classname) and raises a NotImplementedError of no generator
        can be found.

        :param default: Default to a CharField?
        """
        field_name = field.__class__.__name__.lower()
        self.field_name = field_name
        if hasattr(self, 'generate_%s' % field_name):
            return getattr(self, 'generate_%s' % field_name)(field, **kwargs)

        for cls in field.__class__.__bases__:
            cls_name = cls.__name__.lower()
            if hasattr(self, 'generate_%s' % cls_name):
                return getattr(self, 'generate_%s' % cls_name)(field, **kwargs)

        if default:
            # Default to a normal CharField
            # TODO: Somehow add a warning
            defaults = {'required': field.required}

            if hasattr(field, 'min_length'):
                defaults['min_length'] = field.min_length

            if hasattr(field, 'max_length'):
                defaults['max_length'] = field.max_length

            if hasattr(field, 'default'):
                defaults['initial'] = field.default

            defaults.update(kwargs)
            return forms.CharField(**defaults)

        raise NotImplementedError('%s is not supported by MongoForm' %
                                    field.__class__.__name__)

    def get_field_choices(self, field, include_blank=True,
                          blank_choice=BLANK_CHOICE_DASH):
        first_choice = include_blank and blank_choice or []
        return first_choice + list(field.choices)

    def string_field(self, value):
        if value in EMPTY_VALUES:
            return None
        return smart_unicode(value)

    def integer_field(self, value):
        if value in EMPTY_VALUES:
            return None
        return int(value)

    def boolean_field(self, value):
        if value in EMPTY_VALUES:
            return None
        return value.lower() == 'true'

    def get_field_label(self, field):
        if field.verbose_name:
            return field.verbose_name
        if not field.name:
            return ''
        return capfirst(get_verbose_name(field.name))

    def get_field_help_text(self, field):
        if field.help_text:
            return field.help_text.capitalize()

    def generate_stringfield(self, field, **kwargs):
        form_class = MongoCharField

        defaults = {'label': self.get_field_label(field),
                    'initial': field.default,
                    'required': field.required,
                    'help_text': self.get_field_help_text(field)}

        if field.max_length and not field.choices:
            defaults['max_length'] = field.max_length

        if field.max_length is None and not field.choices:
            defaults['widget'] = forms.Textarea

        if field.regex:
            defaults['regex'] = field.regex
        elif field.choices:
            form_class = forms.TypedChoiceField
            defaults['choices'] = self.get_field_choices(field)
            defaults['coerce'] = self.string_field

            if not field.required:
                defaults['empty_value'] = None

        defaults.update(kwargs)
        return form_class(**defaults)

    def generate_emailfield(self, field, **kwargs):
        defaults = {
            'required': field.required,
            'min_length': field.min_length,
            'max_length': field.max_length,
            'initial': field.default,
            'label': self.get_field_label(field),
            'help_text': self.get_field_help_text(field)
        }

        defaults.update(kwargs)
        return forms.EmailField(**defaults)

    def generate_urlfield(self, field, **kwargs):
        defaults = {
            'required': field.required,
            'min_length': field.min_length,
            'max_length': field.max_length,
            'initial': field.default,
            'label': self.get_field_label(field),
            'help_text':  self.get_field_help_text(field)
        }

        defaults.update(kwargs)
        return forms.URLField(**defaults)

    def generate_intfield(self, field, **kwargs):
        if field.choices:
            defaults = {
                'coerce': self.integer_field,
                'empty_value': None,
                'required': field.required,
                'initial': field.default,
                'label': self.get_field_label(field),
                'choices': self.get_field_choices(field),
                'help_text': self.get_field_help_text(field)
            }

            defaults.update(kwargs)
            return forms.TypedChoiceField(**defaults)
        else:
            defaults = {
                'required': field.required,
                'min_value': field.min_value,
                'max_value': field.max_value,
                'initial': field.default,
                'label': self.get_field_label(field),
                'help_text': self.get_field_help_text(field)
            }

            defaults.update(kwargs)
            return forms.IntegerField(**defaults)

    def generate_floatfield(self, field, **kwargs):

        form_class = forms.FloatField

        defaults = {'label': self.get_field_label(field),
                    'initial': field.default,
                    'required': field.required,
                    'min_value': field.min_value,
                    'max_value': field.max_value,
                    'help_text': self.get_field_help_text(field)}

        defaults.update(kwargs)
        return form_class(**defaults)

    def generate_decimalfield(self, field, **kwargs):
        form_class = forms.DecimalField
        defaults = {'label': self.get_field_label(field),
                    'initial': field.default,
                    'required': field.required,
                    'min_value': field.min_value,
                    'max_value': field.max_value,
                    'help_text': self.get_field_help_text(field)}

        defaults.update(kwargs)
        return form_class(**defaults)

    def generate_booleanfield(self, field, **kwargs):
        if field.choices:
            defaults = {
                'coerce': self.boolean_field,
                'empty_value': None,
                'required': field.required,
                'initial': field.default,
                'label': self.get_field_label(field),
                'choices': self.get_field_choices(field),
                'help_text': self.get_field_help_text(field)
            }

            defaults.update(kwargs)
            return forms.TypedChoiceField(**defaults)
        else:
            defaults = {
                'required': field.required,
                'initial': field.default,
                'label': self.get_field_label(field),
                'help_text': self.get_field_help_text(field)
                }

            defaults.update(kwargs)
            return forms.BooleanField(**defaults)

    def generate_datetimefield(self, field, **kwargs):
        defaults = {
            'required': field.required,
            'initial': field.default,
            'label': self.get_field_label(field),
        }

        defaults.update(kwargs)
        return forms.DateTimeField(**defaults)

    def generate_referencefield(self, field, **kwargs):
        defaults = {
            'label': self.get_field_label(field),
            'help_text': self.get_field_help_text(field),
            'required': field.required
        }

        defaults.update(kwargs)
        return ReferenceField(field.document_type.objects, **defaults)

    def generate_listfield(self, field, **kwargs):
        if field.field.choices:
            defaults = {
                'choices': field.field.choices,
                'required': field.required,
                'label': self.get_field_label(field),
                'help_text': self.get_field_help_text(field),
                'widget': forms.CheckboxSelectMultiple
            }

            defaults.update(kwargs)
            return forms.MultipleChoiceField(**defaults)
        elif isinstance(field.field, MongoReferenceField):
            defaults = {
                'label': self.get_field_label(field),
                'help_text': self.get_field_help_text(field),
                'required': field.required
            }

            defaults.update(kwargs)
            f = DocumentMultipleChoiceField(field.field.document_type.objects, **defaults)
            return f

        defaults = {
            'label': self.get_field_label(field),
            'help_text': self.get_field_help_text(field),
            'required': field.required,
            'field_name_base': self.field_name,
            'field': field.field,
            'initial': field.default
        }

        defaults.update(kwargs)
        return ListField(**defaults)

    def generate_filefield(self, field, **kwargs):
        return forms.FileField(**kwargs)

    def generate_imagefield(self, field, **kwargs):
        return forms.ImageField(**kwargs)

    def generate_dictfield(self, field, **kwargs):
        #remove Mongo reserved words
        validate = [RegexValidator(regex='^[^$_]', message=u'Ensure the keys do not begin with : ["$","_"].', code='invalid_start')]
        defaults = {
            'required': field.required,
            'initial': field.default,
            'label': self.get_field_label(field),
            'help_text': self.get_field_help_text(field),
            'validators': validate,
        }
        return DictField(**defaults)


class MongoDefaultFormFieldGenerator(MongoFormFieldGenerator):
    """This class generates Django form-fields for mongoengine-fields."""

    def generate(self, field, **kwargs):
        """Tries to lookup a matching formfield generator (lowercase
        field-classname) and raises a NotImplementedError of no generator
        can be found.
        """
        try:
            return super(MongoDefaultFormFieldGenerator, self).generate(
                        field, **kwargs)
        except NotImplementedError:
            # a normal charfield is always a good guess
            # for a widget.
            # TODO: Somehow add a warning
            defaults = {'required': field.required}

            if hasattr(field, 'min_length'):
                defaults['min_length'] = field.min_length

            if hasattr(field, 'max_length'):
                defaults['max_length'] = field.max_length

            if hasattr(field, 'default'):
                defaults['initial'] = field.default

            defaults.update(kwargs)
            return forms.CharField(**defaults)
