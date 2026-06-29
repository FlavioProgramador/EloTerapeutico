export type LandingIconName =
  | "activity"
  | "calendar"
  | "chart"
  | "clipboard"
  | "file"
  | "lock"
  | "shield"
  | "sparkles"
  | "users"
  | "wallet";

export type ProductTabId = "overview" | "agenda" | "records" | "finance";

export interface ProductTab {
  id: ProductTabId;
  label: string;
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
}

export interface FeatureCard {
  icon: LandingIconName;
  title: string;
  description: string;
  connection: string;
}

export interface ModuleHighlight {
  id: ProductTabId | "patients";
  eyebrow: string;
  title: string;
  description: string;
  benefits: string[];
}

export const navigationLinks = [
  { href: "#produto", label: "Produto" },
  { href: "#recursos", label: "Recursos" },
  { href: "#como-funciona", label: "Como funciona" },
  { href: "#seguranca", label: "Segurança" },
  { href: "#faq", label: "Perguntas" },
];

export const productTabs: ProductTab[] = [
  {
    id: "overview",
    label: "Visão geral",
    eyebrow: "Dashboard clínico",
    title: "A rotina inteira em uma leitura rápida",
    description:
      "Reúna compromissos, pacientes, pendências de prontuário e movimentações financeiras em uma visão operacional única.",
    bullets: [
      "Indicadores do período sem trocar de ferramenta",
      "Ações rápidas para os fluxos mais frequentes",
      "Contexto clínico e administrativo na mesma experiência",
    ],
  },
  {
    id: "agenda",
    label: "Agenda",
    eyebrow: "Organização de atendimentos",
    title: "Horários, pacientes e status conectados",
    description:
      "Planeje sessões, acompanhe confirmações e mantenha cada atendimento associado ao paciente correto.",
    bullets: [
      "Visualização da agenda por período",
      "Status de consultas e horários de atendimento",
      "Integração com pacientes e movimentações financeiras",
    ],
  },
  {
    id: "records",
    label: "Prontuários",
    eyebrow: "Registro clínico",
    title: "Evoluções organizadas ao longo do cuidado",
    description:
      "Registre informações clínicas com histórico, contexto do paciente e controle de acesso por perfil profissional.",
    bullets: [
      "Linha do tempo de evoluções",
      "Vínculo entre atendimento, paciente e profissional",
      "Campos sensíveis tratados pela camada de proteção do sistema",
    ],
  },
  {
    id: "finance",
    label: "Financeiro",
    eyebrow: "Controle da operação",
    title: "Receitas e pendências sem planilhas paralelas",
    description:
      "Acompanhe lançamentos, vencimentos e pagamentos relacionados à rotina de atendimento.",
    bullets: [
      "Receitas e despesas categorizadas",
      "Status de pagamento e vencimentos",
      "Relacionamento com pacientes e consultas",
    ],
  },
];

export const featureCards: FeatureCard[] = [
  {
    icon: "users",
    title: "Gestão de pacientes",
    description:
      "Centralize dados cadastrais, contatos, status e informações necessárias para acompanhar cada pessoa atendida.",
    connection: "Base para agenda, prontuários e financeiro.",
  },
  {
    icon: "calendar",
    title: "Agenda integrada",
    description:
      "Organize sessões, horários, recorrências e mudanças de status em um fluxo conectado ao restante da plataforma.",
    connection: "Conecta atendimento, paciente e cobrança.",
  },
  {
    icon: "clipboard",
    title: "Prontuário e evoluções",
    description:
      "Mantenha registros clínicos estruturados, com histórico e contexto do atendimento associado.",
    connection: "Relaciona evolução, consulta e profissional.",
  },
  {
    icon: "wallet",
    title: "Controle financeiro",
    description:
      "Registre receitas e despesas, acompanhe vencimentos e identifique movimentações pendentes ou concluídas.",
    connection: "Reduz controles financeiros paralelos.",
  },
  {
    icon: "chart",
    title: "Painel operacional",
    description:
      "Visualize as informações mais relevantes da rotina em um dashboard objetivo e orientado a ação.",
    connection: "Resume dados dos módulos principais.",
  },
  {
    icon: "shield",
    title: "Acesso por perfil",
    description:
      "Separe responsabilidades entre administração, profissionais e equipe de apoio conforme as regras do sistema.",
    connection: "Ajuda a limitar o acesso a áreas sensíveis.",
  },
];

export const workflowSteps = [
  {
    number: "01",
    title: "Crie sua conta",
    description:
      "Cadastre o acesso profissional e entre no ambiente de gestão do Elo Terapêutico.",
  },
  {
    number: "02",
    title: "Organize os pacientes",
    description:
      "Registre as informações essenciais para formar a base dos atendimentos.",
  },
  {
    number: "03",
    title: "Conduza a rotina",
    description:
      "Use agenda, prontuários e financeiro dentro de um fluxo conectado.",
  },
  {
    number: "04",
    title: "Acompanhe a operação",
    description:
      "Consulte o dashboard e identifique compromissos, pendências e movimentações.",
  },
];

export const moduleHighlights: ModuleHighlight[] = [
  {
    id: "agenda",
    eyebrow: "Agenda e pacientes",
    title: "Menos retrabalho entre cadastro e atendimento",
    description:
      "A agenda utiliza o contexto do paciente e do profissional para manter os atendimentos organizados, facilitar alterações de status e alimentar os demais módulos.",
    benefits: [
      "Consultas vinculadas ao paciente correto",
      "Visão diária da rotina profissional",
      "Fluxo preparado para recorrências e confirmações",
    ],
  },
  {
    id: "records",
    eyebrow: "Prontuários",
    title: "Continuidade clínica com histórico estruturado",
    description:
      "As evoluções ficam associadas ao atendimento e ao paciente, ajudando o profissional a recuperar contexto sem depender de anotações dispersas.",
    benefits: [
      "Histórico clínico centralizado",
      "Relações claras entre registros e sessões",
      "Acesso restrito conforme o perfil do usuário",
    ],
  },
  {
    id: "finance",
    eyebrow: "Financeiro",
    title: "Visibilidade sobre o que entrou e o que ainda está pendente",
    description:
      "O módulo financeiro acompanha lançamentos, vencimentos e pagamentos para reduzir planilhas paralelas e aproximar a operação administrativa dos atendimentos.",
    benefits: [
      "Receitas e despesas em um só fluxo",
      "Status de pagamento e vencimentos",
      "Integração com consultas e pacientes",
    ],
  },
];

export const securityPoints = [
  {
    icon: "lock" as LandingIconName,
    title: "Dados sensíveis tratados pelo sistema",
    description:
      "O projeto possui uma camada própria para proteção de campos clínicos sensíveis e evolução contínua dos controles de segurança.",
  },
  {
    icon: "users" as LandingIconName,
    title: "Permissões por responsabilidade",
    description:
      "As áreas disponíveis variam conforme o papel do usuário, reduzindo a exposição desnecessária de informações clínicas.",
  },
  {
    icon: "activity" as LandingIconName,
    title: "Rastreabilidade operacional",
    description:
      "A arquitetura inclui trilha de auditoria para apoiar o acompanhamento de ações relevantes dentro da plataforma.",
  },
];

export const faqItems = [
  {
    question: "Para quem o Elo Terapêutico foi criado?",
    answer:
      "A plataforma foi projetada para psicólogos, terapeutas e equipes que precisam organizar pacientes, agenda, registros clínicos e financeiro em uma única rotina digital.",
  },
  {
    question: "Quais módulos já fazem parte do projeto?",
    answer:
      "O projeto possui dashboard, pacientes, agenda, prontuários e controle financeiro. Alguns fluxos continuam sendo aprimorados e são apresentados na interface conforme o estado real de implementação.",
  },
  {
    question: "A equipe de apoio pode acessar prontuários?",
    answer:
      "O sistema diferencia perfis e restringe áreas clínicas para usuários sem a responsabilidade profissional necessária. As permissões finais dependem da configuração e das regras aplicadas no ambiente.",
  },
  {
    question: "A plataforma funciona em celular e tablet?",
    answer:
      "A interface é responsiva e foi estruturada para se adaptar a celulares, tablets, notebooks e monitores maiores.",
  },
  {
    question: "Os dados clínicos ficam misturados com o financeiro?",
    answer:
      "Os módulos se conectam por relacionamentos controlados, mas cada área possui sua própria responsabilidade. Isso permite acompanhar a operação sem transformar dados clínicos em informações financeiras.",
  },
  {
    question: "O produto já está finalizado?",
    answer:
      "O Elo Terapêutico está em desenvolvimento contínuo. A landing page apresenta os módulos implementados e evita anunciar como disponível qualquer recurso que ainda não faça parte do produto.",
  },
];
