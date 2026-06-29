"""Ajustes de resposta para ações de ciclo de vida das evoluções."""

from rest_framework.response import Response

from .clinical_views import EvolutionFinalizeView


class EvolutionFinalizeFreshView(EvolutionFinalizeView):
    """Finaliza a evolução e serializa uma instância recarregada do banco."""

    def post(self, request, pk):
        response = super().post(request, pk)
        if response.status_code >= 400:
            return response

        evolution = self.get_evolution(pk)
        return Response(self.serialize_evolution(evolution, request))
