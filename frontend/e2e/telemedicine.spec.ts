import { expect, test } from "@playwright/test";

const token = process.env.E2E_TELEMEDICINE_TOKEN;

test.describe("telemedicina segura", () => {
  test("remove o convite da URL, registra consentimento e abre a pré-entrada", async ({
    page,
  }) => {
    expect(token, "E2E_TELEMEDICINE_TOKEN deve ser configurado").toBeTruthy();

    await page.goto(
      `/consulta-online/paciente#token=${encodeURIComponent(token || "")}`,
    );

    await expect(page).toHaveURL(/\/consulta-online\/paciente$/);
    await expect(
      page.getByRole("heading", { name: "Antes de entrar no atendimento" }),
    ).toBeVisible();
    await expect(page.getByText("Sem gravação")).toBeVisible();
    await expect(page.locator("body")).not.toContainText(token || "");

    await page.getByRole("checkbox").check();
    await page
      .getByRole("button", { name: "Aceitar e testar dispositivos" })
      .click();

    await expect(
      page.getByRole("heading", { name: "Confira seus dispositivos" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Entrar no atendimento" }),
    ).toBeVisible();

    const browserState = await page.evaluate(() => ({
      hash: window.location.hash,
      local: Object.entries(window.localStorage),
      session: Object.entries(window.sessionStorage),
    }));

    expect(browserState.hash).toBe("");
    expect(JSON.stringify(browserState.local)).not.toContain(token || "");
    expect(JSON.stringify(browserState.session)).not.toContain(token || "");
    expect(JSON.stringify(browserState)).not.toMatch(
      /e2ee_key|access_token|livekit/i,
    );
  });

  test("convite ausente falha de forma genérica", async ({ page }) => {
    await page.goto("/consulta-online/paciente");

    await expect(
      page.getByText("O convite é inválido ou não está mais disponível."),
    ).toBeVisible();
    await expect(page.locator("body")).not.toContainText(
      /Traceback|Internal Server Error/i,
    );
  });
});
