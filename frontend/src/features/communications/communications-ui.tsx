"use client";

import { Bell, Mail, MessageCircle, Send, Smartphone } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { CommunicationChannel, CommunicationStatus } from "./types";

export function statusTone(status: CommunicationStatus) { if (["delivered", "read", "responded"].includes(status)) return "border-success/20 bg-success/10 text-success"; if (["failed", "expired"].includes(status)) return "border-danger/20 bg-danger/10 text-danger"; if (["scheduled", "queued", "processing"].includes(status)) return "border-warning/20 bg-warning/10 text-warning"; return "border-border bg-secondary text-muted-foreground"; }
export function channelIcon(channel: CommunicationChannel) { if (channel === "email") return Mail; if (channel === "in_app") return Bell; if (channel.startsWith("whatsapp")) return MessageCircle; return Smartphone; }
export function formatDate(value?: string | null) { if (!value) return "—"; return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)); }
export function Metric({ title, value, icon: Icon, detail }: { title: string; value: string | number; icon: typeof Send; detail: string }) { return <Card className="border-border bg-card"><CardContent className="flex items-start justify-between p-5"><div><p className="text-xs font-semibold text-muted-foreground">{title}</p><p className="mt-2 text-2xl font-bold text-foreground">{value}</p><p className="mt-1 text-[11px] text-muted-foreground">{detail}</p></div><span className="grid h-10 w-10 place-items-center rounded-xl border border-primary/20 bg-primary/10 text-primary"><Icon className="h-5 w-5" /></span></CardContent></Card>; }
