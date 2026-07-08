from django.db.models import Q

from .filters import PatientFilter


def filter_search(self, queryset, name, value):
    term = (value or "").strip()
    if not term:
        return queryset
    digits = "".join(filter(str.isdigit, term))
    query = (
        Q(full_name__icontains=term)
        | Q(social_name__icontains=term)
        | Q(email__icontains=term)
        | Q(phone__icontains=term)
        | Q(whatsapp__icontains=term)
    )
    if digits:
        query |= Q(cpf__icontains=digits)
        if len(digits) == 10:
            formatted = f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
            query |= Q(phone__icontains=formatted) | Q(whatsapp__icontains=formatted)
        elif len(digits) == 11:
            formatted = f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
            query |= Q(phone__icontains=formatted) | Q(whatsapp__icontains=formatted)
    return queryset.filter(query).distinct()


PatientFilter.filter_search = filter_search
