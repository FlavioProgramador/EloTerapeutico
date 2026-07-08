import { Reveal } from "./motion";

const testimonials = [
  {
    name: "Dra. Marina Costa",
    specialty: "Psicóloga Clínica",
    quote:
      "Antes eu perdia tempo/juntando dados de agenda, WhatsApp e planilha. Agora tudo está num lugar só e posso focar no que importa: meus pacientes.",
    avatar: "MC",
  },
  {
    name: "Ricardo Mendes",
    specialty: "Terapeuta Holístico",
    quote:
      "O financeiro conectado à agenda me economiza horas por semana. Não preciso mais cruzar planilhas para saber quem pagou.",
    avatar: "RM",
  },
  {
    name: "Ana Luiza Ferreira",
    specialty: "Psicanalista",
    quote:
      "A segurança dos prontuários me deu tranquilidade. Sei que meus dados e os dos meus pacientes estão protegidos.",
    avatar: "AL",
  },
];

export function Testimonials() {
  return (
    <section className="testimonials" aria-label="Depoimentos">
      <div className="testimonials__inner">
        <Reveal className="testimonials__heading">
          <span className="landing-eyebrow">Quem já usa</span>
          <h2>O que terapeutas estão dizendo.</h2>
          <p>
            Depoimentos de profissionais que já organizaram sua rotina com o Elo Terapêutico.
          </p>
        </Reveal>

        <div className="testimonials__grid">
          {testimonials.map((t, i) => (
            <Reveal key={t.name} className="testimonials__card" delay={i * 0.06}>
              <blockquote>
                <p>&ldquo;{t.quote}&rdquo;</p>
              </blockquote>
              <div className="testimonials__author">
                <span className="testimonials__avatar" aria-hidden="true">
                  {t.avatar}
                </span>
                <div>
                  <strong>{t.name}</strong>
                  <small>{t.specialty}</small>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
