"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  Archive,
  CheckSquare,
  ClipboardList,
  Copy,
  Eye,
  FileText,
  GripVertical,
  Hash,
  Heading,
  ListChecks,
  Loader2,
  Pencil,
  Plus,
  RotateCcw,
  Save,
  Search,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { formsService } from "./forms.service";
import {
  useCreateForm,
  useCreateFormFromTemplate,
  useFormAction,
  useForms,
  useFormTemplates,
  useUpdateForm,
} from "./use-forms";
import type {
  FormCategory,
  FormField,
  FormFieldType,
  FormPayload,
  FormTemplate,
  TherapeuticForm,
} from "./types";

const fieldTypes: Array<{ type: FormFieldType; label: string; icon: typeof FileText }> = [
  { type: "short_text", label: "Texto Curto", icon: FileText },
  { type: "long_text", label: "Texto Longo", icon: ListChecks },
  { type: "number", label: "Número", icon: Hash },
  { type: "date", label: "Data", icon: ClipboardList },
  { type: "select", label: "Seleção", icon: ListChecks },
  { type: "radio", label: "Múltipla Escolha", icon: CheckSquare },
  { type: "checkbox", label: "Caixas de Seleção", icon: CheckSquare },
  { type: "scale", label: "Escala", icon: SlidersHorizontal },
  { type: "heading", label: "Título", icon: Heading },
];

const categories: Array<{ value: FormCategory; label: string }> = [
  { value: "anamnese", label: "Anamnese" },
  { value: "avaliacao", label: "Avaliação" },
  { value: "evolucao", label: "Evolução" },
  { value: "escalas", label: "Escalas" },
  { value: "questionario", label: "Questionário" },
  { value: "outro", label: "Outro" },
];

function clientFieldId(field: FormField, index: number) {
  return field.id ?? `tmp-${index + 1}-${field.type}-${crypto.randomUUID()}`;
}

function normalizeClientFields(fields: FormField[] = []) {
  return fields.map((field, index) => ({
    ...field,
    id: clientFieldId(field, index),
    order: field.order || index + 1,
    config: field.config ?? {},
    is_visible: field.is_visible ?? true,
  }));
}

function defaultField(type: FormFieldType, order: number): FormField {
  const labels: Record<FormFieldType, string> = {
    short_text: "Novo Campo de Texto",
    long_text: "Novo Campo de Texto Longo",
    number: "Novo Campo Numérico",
    date: "Nova Data",
    select: "Nova Seleção",
    radio: "Nova Múltipla Escolha",
    checkbox: "Novas Caixas de Seleção",
    scale: "Nova Escala",
    heading: "Seção",
  };
  const config =
    type === "scale"
      ? { min: 1, max: 10, step: 1, min_label: "1", max_label: "10" }
      : ["select", "radio", "checkbox"].includes(type)
        ? { options: ["Opção 1", "Opção 2"] }
        : type === "long_text"
          ? { rows: 4, max_length: 2000 }
          : { max_length: 255 };

  return {
    id: `tmp-${crypto.randomUUID()}`,
    type,
    label: labels[type],
    placeholder: type === "heading" ? "" : "Digite aqui...",
    help_text: "",
    required: false,
    order,
    is_visible: true,
    config,
  };
}

function fieldIcon(type: FormFieldType) {
  return fieldTypes.find((item) => item.type === type)?.icon ?? FileText;
}

function categoryBadge(category: FormCategory) {
  const tones: Record<FormCategory, string> = {
    anamnese: "bg-primary/15 text-primary border-primary/20",
    avaliacao: "bg-purple-500/15 text-purple-300 border-purple-500/20",
    evolucao: "bg-success/15 text-success border-success/20",
    escalas: "bg-warning/15 text-warning border-warning/20",
    questionario: "bg-sky-500/15 text-sky-300 border-sky-500/20",
    outro: "bg-secondary text-muted-foreground border-border",
  };
  return tones[category] ?? tones.outro;
}

function inputClass(className?: string) {
  return cn(
    "h-11 rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus:border-primary",
    className,
  );
}

function Modal({ children, onClose, wide = false }: { children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-background/70 p-4 backdrop-blur-md">
      <div className={cn("max-h-[92vh] w-full overflow-y-auto rounded-2xl border border-primary/20 bg-card shadow-2xl shadow-black/40", wide ? "max-w-5xl" : "max-w-3xl")}>
        <button type="button" onClick={onClose} className="float-right m-5 rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  );
}

function FieldPreview({ field }: { field: FormField }) {
  if (field.is_visible === false) return null;
  if (field.type === "heading") {
    return (
      <div className="pt-2">
        <h3 className="text-base font-bold text-foreground">{field.label}</h3>
        {field.help_text && <p className="mt-1 text-xs text-muted-foreground">{field.help_text}</p>}
      </div>
    );
  }

  const options = field.config.options ?? ["Opção 1", "Opção 2"];
  return (
    <label className="grid gap-2">
      <span className="text-sm font-semibold text-foreground">
        {field.label}
        {field.required && <b className="text-danger"> *</b>}
      </span>
      {field.help_text && <span className="text-xs text-muted-foreground">{field.help_text}</span>}
      {field.type === "long_text" && <textarea className={inputClass("h-24 py-3")} placeholder={field.placeholder || "Digite aqui..."} />}
      {field.type === "short_text" && <input className={inputClass()} placeholder={field.placeholder || "Digite aqui..."} />}
      {field.type === "number" && <input type="number" className={inputClass()} placeholder={field.placeholder || "0"} />}
      {field.type === "date" && <input type="date" className={inputClass()} />}
      {field.type === "select" && (
        <select className={inputClass()}>
          <option>Selecione...</option>
          {options.map((item, index) => <option key={`${field.id}-option-${index}-${item}`}>{item}</option>)}
        </select>
      )}
      {field.type === "radio" && (
        <span className="grid gap-2">
          {options.map((item, index) => <span key={`${field.id}-radio-${index}-${item}`} className="flex items-center gap-2 text-sm text-muted-foreground"><input type="radio" name={String(field.id)} />{item}</span>)}
        </span>
      )}
      {field.type === "checkbox" && (
        <span className="grid gap-2">
          {options.map((item, index) => <span key={`${field.id}-checkbox-${index}-${item}`} className="flex items-center gap-2 text-sm text-muted-foreground"><input type="checkbox" />{item}</span>)}
        </span>
      )}
      {field.type === "scale" && (
        <span className="grid gap-2">
          <input type="range" min={field.config.min ?? 1} max={field.config.max ?? 10} step={field.config.step ?? 1} defaultValue={field.config.default_value ?? field.config.min ?? 1} />
          <span className="flex justify-between text-xs text-muted-foreground">
            <span>{field.config.min_label ?? field.config.min ?? 1}</span>
            <span>{field.config.max_label ?? field.config.max ?? 10}</span>
          </span>
        </span>
      )}
    </label>
  );
}

function TemplateModal({ onClose, onUse }: { onClose: () => void; onUse: (template: FormTemplate) => void }) {
  const templates = useFormTemplates({ page_size: 20 });
  return (
    <Modal onClose={onClose}>
      <div className="p-7">
        <h2 className="text-xl font-bold">Criar a partir de Template</h2>
        <p className="mt-2 text-sm text-muted-foreground">Escolha um template para começar com campos pré-configurados. Você pode personalizar o formulário depois.</p>
        {templates.isLoading && <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Carregando templates...</div>}
        {templates.isError && <p className="mt-6 text-sm text-danger">Não foi possível carregar os templates.</p>}
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {templates.data?.results.map((template) => (
            <button key={template.id} type="button" onClick={() => onUse(template)} className="rounded-xl border border-primary/15 bg-secondary/40 p-4 text-left transition hover:-translate-y-0.5 hover:border-primary/40 hover:bg-secondary">
              <div className="flex gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/15 text-primary"><ClipboardList className="h-5 w-5" /></span>
                <span>
                  <strong className="block text-sm text-foreground">{template.name}</strong>
                  <span className="mt-1 block text-xs text-muted-foreground">{template.description}</span>
                  <span className="mt-3 flex gap-2">
                    <b className={cn("rounded-full border px-2 py-1 text-[10px]", categoryBadge(template.category))}>{template.category_display}</b>
                    <b className="rounded-full border border-border px-2 py-1 text-[10px] text-muted-foreground">{template.fields_count} campos</b>
                  </span>
                </span>
              </div>
            </button>
          ))}
        </div>
        {templates.data?.results.length === 0 && <p className="mt-6 text-sm text-muted-foreground">Nenhum template disponível.</p>}
      </div>
    </Modal>
  );
}

function FieldSettings({ field, onChange }: { field: FormField; onChange: (field: FormField) => void }) {
  const needsOptions = ["select", "radio", "checkbox"].includes(field.type);
  const set = (patch: Partial<FormField>) => onChange({ ...field, ...patch });
  const setConfig = (patch: Record<string, unknown>) => onChange({ ...field, config: { ...field.config, ...patch } });

  return (
    <div className="mt-3 grid gap-3 rounded-xl border border-border bg-background/40 p-3">
      <input className={inputClass()} value={field.label} onChange={(event) => set({ label: event.target.value })} placeholder="Label" />
      <input className={inputClass()} value={field.placeholder ?? ""} onChange={(event) => set({ placeholder: event.target.value })} placeholder="Placeholder" />
      <input className={inputClass()} value={field.help_text ?? ""} onChange={(event) => set({ help_text: event.target.value })} placeholder="Texto de ajuda" />
      <label className="flex items-center gap-2 text-xs text-muted-foreground">
        <input type="checkbox" checked={Boolean(field.required)} onChange={(event) => set({ required: event.target.checked })} /> Campo obrigatório
      </label>
      {needsOptions && <textarea className={inputClass("h-24 py-3")} value={(field.config.options ?? []).join("\n")} onChange={(event) => setConfig({ options: event.target.value.split("\n").filter(Boolean) })} placeholder="Uma opção por linha" />}
      {field.type === "scale" && <div className="grid grid-cols-2 gap-2"><input type="number" className={inputClass()} value={field.config.min ?? 1} onChange={(event) => setConfig({ min: Number(event.target.value) })} /><input type="number" className={inputClass()} value={field.config.max ?? 10} onChange={(event) => setConfig({ max: Number(event.target.value) })} /></div>}
    </div>
  );
}

function BuilderModal({ initial, templateId, onClose }: { initial?: Partial<FormPayload> & { id?: number }; templateId?: number; onClose: () => void }) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [category, setCategory] = useState<FormCategory>(initial?.category ?? "anamnese");
  const [fields, setFields] = useState<FormField[]>(() => normalizeClientFields(initial?.fields ?? []));
  const [tab, setTab] = useState<"editor" | "preview">("editor");
  const [editing, setEditing] = useState<string | number | null>(null);
  const createForm = useCreateForm();
  const updateForm = useUpdateForm();
  const createFromTemplate = useCreateFormFromTemplate();
  const saving = createForm.isPending || updateForm.isPending || createFromTemplate.isPending;
  const isEditing = typeof initial?.id === "number";

  function addField(type: FormFieldType) {
    setFields((current) => [...current, defaultField(type, current.length + 1)]);
  }

  function updateField(updated: FormField) {
    setFields((current) => current.map((item) => item.id === updated.id ? updated : item));
  }

  function removeField(id: string | number | undefined) {
    setFields((current) => current.filter((item) => item.id !== id).map((item, index) => ({ ...item, order: index + 1 })));
  }

  function duplicateField(field: FormField) {
    setFields((current) => [...current, { ...field, id: `tmp-${crypto.randomUUID()}`, label: `${field.label} (cópia)`, order: current.length + 1 }]);
  }

  function moveField(index: number, direction: -1 | 1) {
    setFields((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const copy = [...current];
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return copy.map((item, orderIndex) => ({ ...item, order: orderIndex + 1 }));
    });
  }

  function validate(): string | null {
    if (!name.trim()) return "Informe o nome do formulário.";
    if (!fields.length) return "Adicione ao menos um campo ao formulário.";
    for (const field of fields) {
      if (!field.label.trim()) return "Todos os campos precisam de nome.";
      if (["select", "radio", "checkbox"].includes(field.type) && !(field.config.options ?? []).length) return "Campos de seleção precisam de opções.";
      if (field.type === "scale" && Number(field.config.min ?? 1) >= Number(field.config.max ?? 10)) return "Escala inválida: mínimo deve ser menor que máximo.";
    }
    return null;
  }

  async function save() {
    const error = validate();
    if (error) return toast.error(error);
    const payload = { name: name.trim(), description, category, fields: fields.map((field, index) => ({ ...field, order: index + 1 })) };
    try {
      if (isEditing) await updateForm.mutateAsync({ id: initial.id!, payload });
      else if (templateId) await createFromTemplate.mutateAsync({ templateId, payload });
      else await createForm.mutateAsync(payload);
      toast.success(isEditing ? "Formulário atualizado." : "Formulário criado.");
      onClose();
    } catch {
      toast.error("Não foi possível salvar o formulário.");
    }
  }

  return (
    <Modal onClose={onClose} wide>
      <div className="p-7">
        <h2 className="text-xl font-bold">{isEditing ? "Editar Formulário" : "Novo Formulário"}</h2>
        <p className="mt-2 text-sm text-muted-foreground">Crie um novo formulário adicionando campos personalizados.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-xs font-semibold">Nome do Formulário *<input className={inputClass()} value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex: Anamnese Adulto" /></label>
          <label className="grid gap-1 text-xs font-semibold">Descrição<input className={inputClass()} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Breve descrição do formulário" /></label>
        </div>
        <div className="mt-3"><select className={inputClass("w-full md:w-64")} value={category} onChange={(event) => setCategory(event.target.value as FormCategory)}>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
        <div className="mt-5 flex border-b border-border">
          <button type="button" onClick={() => setTab("editor")} className={cn("px-5 py-3 text-sm font-semibold", tab === "editor" ? "border-b-2 border-primary text-foreground" : "text-muted-foreground")}>Editor</button>
          <button type="button" onClick={() => setTab("preview")} className={cn("px-5 py-3 text-sm font-semibold", tab === "preview" ? "border-b-2 border-primary text-foreground" : "text-muted-foreground")}>Preview</button>
        </div>

        {tab === "editor" ? (
          <div className="mt-5 grid gap-4 lg:grid-cols-[14rem_1fr]">
            <Card><CardContent className="p-4"><h3 className="text-sm font-bold">Adicionar Campo</h3><div className="mt-3 grid gap-1">{fieldTypes.map((item) => { const Icon = item.icon; return <button key={item.type} type="button" onClick={() => addField(item.type)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold text-muted-foreground hover:bg-primary/10 hover:text-foreground"><Icon className="h-4 w-4 text-primary" />{item.label}</button>; })}</div></CardContent></Card>
            <div className="rounded-xl border border-primary/10 bg-secondary/20 p-4">
              {fields.length === 0 ? <div className="grid min-h-44 place-items-center text-sm text-muted-foreground">Adicione campos para montar o formulário.</div> : (
                <div className="grid gap-3">
                  {fields.map((field, index) => { const Icon = fieldIcon(field.type); return (
                    <div key={field.id} className="rounded-xl border border-primary/15 bg-card p-3">
                      <div className="flex items-center gap-3">
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                        <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/15 text-primary"><Icon className="h-4 w-4" /></span>
                        <button type="button" onClick={() => setEditing(editing === field.id ? null : field.id!)} className="flex-1 text-left"><strong className="block text-sm">{field.label}</strong><span className="text-xs text-muted-foreground">{fieldTypes.find((item) => item.type === field.type)?.label}</span></button>
                        <button type="button" onClick={() => moveField(index, -1)} className="text-xs text-muted-foreground">↑</button>
                        <button type="button" onClick={() => moveField(index, 1)} className="text-xs text-muted-foreground">↓</button>
                        <button type="button" onClick={() => duplicateField(field)} className="rounded-lg p-2 text-muted-foreground hover:bg-secondary"><Copy className="h-4 w-4" /></button>
                        <button type="button" onClick={() => removeField(field.id)} className="rounded-lg p-2 text-danger hover:bg-danger-soft"><Trash2 className="h-4 w-4" /></button>
                      </div>
                      {editing === field.id && <FieldSettings field={field} onChange={updateField} />}
                    </div>
                  ); })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-5 rounded-2xl border border-primary/15 bg-secondary/30 p-6">
            <h3 className="text-lg font-bold">{name || "Formulário sem nome"}</h3>
            <p className="mt-2 text-sm text-muted-foreground">Visualização de como o formulário aparecerá para o usuário</p>
            <div className="mt-6 grid gap-5">{fields.length === 0 ? <p className="text-sm text-muted-foreground">Nenhum campo adicionado.</p> : fields.map((field) => <FieldPreview key={field.id} field={field} />)}</div>
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3 border-t border-border pt-4"><Button variant="outline" onClick={onClose}>Cancelar</Button><Button onClick={save} isLoading={saving} leftIcon={<Save className="h-4 w-4" />}>{isEditing ? "Salvar Alterações" : "Criar Formulário"}</Button></div>
      </div>
    </Modal>
  );
}

function FormCard({ form, onEdit }: { form: TherapeuticForm; onEdit: (form: TherapeuticForm) => void }) {
  const duplicate = useFormAction("duplicate");
  const archive = useFormAction(form.status === "active" ? "archive" : "restore");
  const remove = useFormAction("remove");

  async function run(action: "duplicate" | "archive" | "remove") {
    try {
      if (action === "duplicate") await duplicate.mutateAsync(form.id);
      if (action === "archive") await archive.mutateAsync(form.id);
      if (action === "remove") await remove.mutateAsync(form.id);
      toast.success("Ação realizada com sucesso.");
    } catch {
      toast.error("Não foi possível concluir a ação.");
    }
  }

  return (
    <Card className="border-primary/10 bg-card/95">
      <CardContent className="p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2"><h3 className="text-base font-bold">{form.name}</h3><span className={cn("rounded-full border px-2 py-1 text-[10px] font-bold", categoryBadge(form.category))}>{form.category_display}</span><span className={cn("rounded-full px-2 py-1 text-[10px] font-bold", form.status === "active" ? "bg-success/15 text-success" : "bg-muted text-muted-foreground")}>{form.status_display}</span></div>
            <p className="mt-2 text-sm text-muted-foreground">{form.description || "Sem descrição"}</p>
            <p className="mt-3 text-xs text-muted-foreground">{form.fields_count} campos • Criado por {form.created_by_name || "-"} • Atualizado em {new Date(form.updated_at).toLocaleDateString("pt-BR")}</p>
          </div>
          <div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" leftIcon={<Eye className="h-4 w-4" />} onClick={() => onEdit(form)}>Visualizar</Button><Button size="sm" variant="outline" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => onEdit(form)}>Editar</Button><Button size="sm" variant="outline" leftIcon={<Copy className="h-4 w-4" />} onClick={() => run("duplicate")}>Duplicar</Button><Button size="sm" variant="outline" leftIcon={form.status === "active" ? <Archive className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />} onClick={() => run("archive")}>{form.status === "active" ? "Arquivar" : "Restaurar"}</Button><Button size="sm" variant="destructive" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => run("remove")}>Excluir</Button></div>
        </div>
      </CardContent>
    </Card>
  );
}

export function FormsPage() {
  const [search, setSearch] = useState("");
  const [showTemplate, setShowTemplate] = useState(false);
  const [builder, setBuilder] = useState<{ initial?: Partial<FormPayload> & { id?: number }; templateId?: number } | null>(null);
  const filters = useMemo(() => ({ search, page_size: 50 }), [search]);
  const forms = useForms(filters);
  const list = forms.data?.results ?? [];

  function useTemplate(template: FormTemplate) {
    setShowTemplate(false);
    setBuilder({ templateId: template.id, initial: { name: template.name, description: template.description, category: template.category, fields: normalizeClientFields(template.fields_schema) } });
  }

  async function editForm(form: TherapeuticForm) {
    try {
      const freshForm = await formsService.get(form.id);
      setBuilder({ initial: { id: freshForm.id, name: freshForm.name, description: freshForm.description, category: freshForm.category, fields: normalizeClientFields(freshForm.fields) } });
    } catch {
      setBuilder({ initial: { id: form.id, name: form.name, description: form.description, category: form.category, fields: normalizeClientFields(form.fields) } });
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><div className="flex items-center gap-2"><h1 className="text-2xl font-bold tracking-tight">Formulários</h1><ClipboardList className="h-4 w-4 text-muted-foreground" /></div><p className="mt-1 text-sm text-muted-foreground">Crie formulários personalizados para anamnese, avaliações e questionários</p></div><div className="flex gap-2"><Button variant="outline" leftIcon={<ClipboardList className="h-4 w-4" />} onClick={() => setShowTemplate(true)}>Usar Template</Button><Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setBuilder({})}>Novo Formulário</Button></div></header>
      <div className="relative max-w-md"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><input className={inputClass("w-full pl-9")} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar formulários..." /></div>
      {forms.isLoading && <div className="h-56 animate-pulse rounded-2xl border border-border bg-card" />}
      {forms.isError && <Card><CardContent className="grid min-h-52 place-items-center text-center"><div><p className="font-bold text-danger">Não foi possível carregar os formulários.</p><Button className="mt-4" variant="outline" onClick={() => forms.refetch()}>Tentar novamente</Button></div></CardContent></Card>}
      {!forms.isLoading && !forms.isError && list.length === 0 && <Card className="border-primary/10 bg-card/95"><CardContent className="grid min-h-64 place-items-center p-8 text-center"><div><span className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-primary/15 text-primary"><ClipboardList className="h-8 w-8" /></span><h2 className="mt-5 text-lg font-bold">{search ? "Nenhum formulário encontrado para essa busca." : "Nenhum formulário encontrado"}</h2><p className="mt-2 text-sm text-muted-foreground">Comece criando seu primeiro formulário personalizado.</p><Button className="mt-5" leftIcon={<Plus className="h-4 w-4" />} onClick={() => setBuilder({})}>Criar Primeiro Formulário</Button></div></CardContent></Card>}
      {list.length > 0 && <div className="grid gap-3">{list.map((form) => <FormCard key={form.id} form={form} onEdit={editForm} />)}</div>}
      {showTemplate && <TemplateModal onClose={() => setShowTemplate(false)} onUse={useTemplate} />}
      {builder && <BuilderModal initial={builder.initial} templateId={builder.templateId} onClose={() => setBuilder(null)} />}
    </div>
  );
}
