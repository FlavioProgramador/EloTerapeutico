import { redirect } from "next/navigation";

type CadastroPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CadastroPage({ searchParams }: CadastroPageProps) {
  const params = await searchParams;
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => query.append(key, item));
    } else if (value) {
      query.set(key, value);
    }
  });

  redirect(`/register${query.size ? `?${query.toString()}` : ""}`);
}
