from django.shortcuts import render
from django.views.generic import DetailView
from django.db.models import Q
from .models import Option, OptionRelation

# Create your views here.

class OptionDetailView(DetailView):
    """
    Abstract base view for displaying option details and relationships.
    Inherit from this view and set template_name in your concrete view.
    """
    model = Option
    context_object_name = 'option'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        option = self.object

        # Get all relations where this option is either the from_option or to_option
        relations = OptionRelation.objects.filter(
            Q(from_option=option) | Q(to_option=option)
        ).select_related(
            'from_option', 'to_option', 
            'relation_type',
            'from_option__group', 'to_option__group'
        )

        # Split relations into outgoing and incoming
        context['outgoing_relations'] = [
            rel for rel in relations if rel.from_option_id == option.id
        ]
        context['incoming_relations'] = [
            rel for rel in relations if rel.to_option_id == option.id
        ]

        return context
