"use client";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { useAppointmentForm } from "../hooks/use-appointment-form";
import { AppointmentAdministrativeSection } from "./appointment-form/appointment-administrative-section";
import { AppointmentDetailsSection } from "./appointment-form/appointment-details-section";
import { AppointmentOptionsSection } from "./appointment-form/appointment-options-section";
import { AppointmentWhoWhenSection } from "./appointment-form/appointment-who-when-section";

interface AppointmentModalProps {
  open: boolean;
  defaultDate: Date;
  defaultTime?: string;
  onClose: () => void;
}

export function AppointmentModal({
  open,
  defaultDate,
  defaultTime = "09:00",
  onClose,
}: AppointmentModalProps) {
  const appointmentForm = useAppointmentForm({
    open,
    defaultDate,
    defaultTime,
    onSuccess: onClose,
  });

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Nova consulta"
      description="Todos os campos essenciais em uma única tela."
      className="max-w-4xl"
    >
      <form
        onSubmit={appointmentForm.submit}
        className="grid gap-6 lg:grid-cols-2"
      >
        <div className="space-y-5">
          <AppointmentWhoWhenSection
            form={appointmentForm.form}
            setForm={appointmentForm.setForm}
            search={appointmentForm.search}
            onSearchChange={appointmentForm.setSearch}
            patients={appointmentForm.patients}
            professionals={appointmentForm.professionals}
            slots={appointmentForm.slots}
            loadingSlots={appointmentForm.loadingSlots}
            showTherapistField={appointmentForm.showTherapistField}
            onApplySlot={appointmentForm.applySlot}
          />
          <AppointmentDetailsSection
            form={appointmentForm.form}
            setForm={appointmentForm.setForm}
            rooms={appointmentForm.rooms}
          />
        </div>

        <div className="space-y-5">
          <AppointmentOptionsSection
            form={appointmentForm.form}
            setForm={appointmentForm.setForm}
          />
          <AppointmentAdministrativeSection
            form={appointmentForm.form}
            setForm={appointmentForm.setForm}
            duration={appointmentForm.duration}
          />
        </div>

        <div className="flex justify-end gap-2 border-t border-border pt-4 lg:col-span-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={appointmentForm.isSubmitting}>
            Agendar consulta
          </Button>
        </div>
      </form>
    </Modal>
  );
}
