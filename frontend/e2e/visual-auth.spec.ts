import { expect, test } from "@playwright/test";

const TECHNICAL_CONTENT =
  /(?:EMAIL_BACKEND|DEFAULT_FROM_EMAIL|Traceback|Internal Server Error|Connection refused|ECONNREFUSED)/i;

const ORANGE_PRIMARY_TOKENS = ["27 86% 54%", "27 90% 59%"];
const CHARCOAL_SIDEBAR_TOKENS = ["24 18% 12%", "24 18% 6%"];

test("login mantém ilustração original e identidade laranja", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/login");

  const illustration = page.getByAltText(
    "Ilustração de um ambiente terapêutico acolhedor",
  );
  await expect(illustration).toBeVisible();
  await expect(illustration).toHaveAttribute("src", /login_illustration\.svg/);
  await expect(page.locator("body")).not.toContainText(TECHNICAL_CONTENT);

  const theme = await page.evaluate(() => {
    const styles = getComputedStyle(document.documentElement);
    return {
      primary: styles.getPropertyValue("--primary").trim(),
      sidebar: styles.getPropertyValue("--sidebar").trim(),
    };
  });

  expect(ORANGE_PRIMARY_TOKENS).toContain(theme.primary);
  expect(CHARCOAL_SIDEBAR_TOKENS).toContain(theme.sidebar);
  expect(theme.primary).not.toMatch(/(?:142|149|159|177)\s/);
  expect(theme.sidebar).not.toMatch(/(?:142|149|159|177)\s/);
});

test("cadastro restaura ilustração original e resumo laranja", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/register");

  const illustration = page.getByAltText(
    "Ilustração de um ambiente terapêutico acolhedor",
  );
  await expect(illustration).toBeVisible();
  await expect(illustration).toHaveAttribute("src", /register_illustration\.svg/);
  await expect(page.getByText("Resumo da contratação")).toBeVisible();
  await expect(page.locator("body")).not.toContainText(TECHNICAL_CONTENT);
});

test("autenticação continua responsiva sem rolagem horizontal", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });

  for (const path of ["/login", "/register"]) {
    await page.goto(path);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  }
});
