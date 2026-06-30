import { PatientBrowserSafe } from "./patient-browser-safe";

export function PatientBrowserFinal() {
  return (
    <div className="[&>div>header>button]:hidden">
      <PatientBrowserSafe />
    </div>
  );
}
