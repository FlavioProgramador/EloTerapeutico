def serialize_patient_professionals(patient):
    links = patient.professional_links.filter(is_active=True).select_related("professional")
    data = [
        {
            "id": link.professional_id,
            "full_name": link.professional.full_name,
            "specialty": link.professional.specialty,
            "is_primary": link.is_primary,
        }
        for link in links
    ]
    if patient.therapist_id not in {item["id"] for item in data}:
        data.insert(
            0,
            {
                "id": patient.therapist_id,
                "full_name": patient.therapist.full_name,
                "specialty": patient.therapist.specialty,
                "is_primary": True,
            },
        )
    return data
