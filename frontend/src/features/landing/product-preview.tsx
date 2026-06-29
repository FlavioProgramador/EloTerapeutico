"use client";

import { productTabs } from "./content";

export function ProductPreview() {
  return (
    <section id="produto">
      <h2>Veja como os módulos trabalham juntos</h2>
      <p>{productTabs[0].description}</p>
    </section>
  );
}
