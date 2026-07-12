import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#F7FAF8] px-5 py-12 text-[#1A2E26]">
      <article className="mx-auto max-w-3xl rounded-3xl border border-[#1A2E26]/10 bg-white p-7 shadow-sm sm:p-10">
        <Link href="/" className="text-sm font-bold text-[#F97316] hover:underline">← Voltar para a página inicial</Link>
        <h1 className="mt-7 text-4xl font-extrabold">Termos de Uso</h1>
        <p className="mt-4 text-sm leading-7 text-gray-600">Estes termos regulam o uso do Elo Terapêutico. O acesso às ferramentas depende de assinatura ativa ou teste gratuito válido. O usuário permanece responsável pela utilização adequada do sistema e pela veracidade das informações cadastradas.</p>
        <h2 className="mt-8 text-xl font-bold">Assinatura e cobrança</h2>
        <p className="mt-3 text-sm leading-7 text-gray-600">Valores, ciclos, parcelas e recursos são calculados pelo backend conforme o plano selecionado. A ativação ocorre somente após confirmação segura do gateway de pagamento.</p>
        <h2 className="mt-8 text-xl font-bold">Cancelamento e dados</h2>
        <p className="mt-3 text-sm leading-7 text-gray-600">O cancelamento não apaga automaticamente a conta, pacientes, documentos ou prontuários. As regras de retenção e exclusão seguem a legislação aplicável e a Política de Privacidade.</p>
        <p className="mt-8 rounded-2xl bg-[#FFF7ED] p-4 text-xs leading-6 text-gray-600">Texto operacional inicial. Antes do lançamento comercial, a versão final deve ser revisada por assessoria jurídica.</p>
      </article>
    </main>
  );
}
