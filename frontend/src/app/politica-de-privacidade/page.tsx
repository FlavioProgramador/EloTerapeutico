import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#F7FAF8] px-5 py-12 text-[#1A2E26]">
      <article className="mx-auto max-w-3xl rounded-3xl border border-[#1A2E26]/10 bg-white p-7 shadow-sm sm:p-10">
        <Link href="/" className="text-sm font-bold text-[#F97316] hover:underline">← Voltar para a página inicial</Link>
        <h1 className="mt-7 text-4xl font-extrabold">Política de Privacidade</h1>
        <p className="mt-4 text-sm leading-7 text-gray-600">O Elo Terapêutico trata dados de conta, cobrança e operação do consultório para prestar o serviço. Dados clínicos não são enviados ao gateway de pagamento.</p>
        <h2 className="mt-8 text-xl font-bold">Dados de pagamento</h2>
        <p className="mt-3 text-sm leading-7 text-gray-600">O sistema armazena apenas identificadores, status, valores, faturas e links necessários à conciliação. Dados completos de cartão e chaves do gateway não são armazenados no frontend.</p>
        <h2 className="mt-8 text-xl font-bold">Segurança e retenção</h2>
        <p className="mt-3 text-sm leading-7 text-gray-600">Acesso é controlado por autenticação, autorização, assinatura e isolamento por usuário. O término da assinatura bloqueia ferramentas, mas não apaga automaticamente os dados.</p>
        <p className="mt-8 rounded-2xl bg-[#ECFDF5] p-4 text-xs leading-6 text-gray-600">Texto operacional inicial. A versão definitiva deve indicar controlador, encarregado, bases legais, prazos de retenção e canais para exercício de direitos previstos na LGPD.</p>
      </article>
    </main>
  );
}
