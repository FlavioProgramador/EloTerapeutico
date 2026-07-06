import fs from "node:fs";

const input = process.argv[2] ?? "coverage-output.txt";
const output = process.argv[3] ?? "coverage-summary.json";
const text = fs.readFileSync(input, "utf8");
const match = text.match(
  /all files\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)/i,
);

if (!match) {
  throw new Error("Não foi possível localizar o resumo de cobertura do frontend.");
}

const summary = {
  lines: Number(match[1]),
  branches: Number(match[2]),
  functions: Number(match[3]),
};

fs.writeFileSync(output, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

const githubOutput = process.env.GITHUB_OUTPUT;
if (githubOutput) {
  fs.appendFileSync(
    githubOutput,
    `lines=${summary.lines}\nbranches=${summary.branches}\nfunctions=${summary.functions}\n`,
    "utf8",
  );
}

console.log(JSON.stringify(summary));
