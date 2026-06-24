/**
 * Script de migração v3: converte toast({}) para API sonner.
 * Usa uma máquina de estados simples para capturar blocos multiline.
 */

import { readFileSync, writeFileSync } from 'fs';

const files = [
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/agenda/page.tsx',
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/financeiro/page.tsx',
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/patients/[id]/page.tsx',
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/patients/page.tsx',
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/records/[patientId]/page.tsx',
  'd:/Projetos/elo-terapeutico/frontend/src/app/dashboard/records/page.tsx',
];

const variantMap = {
  success: 'toast.success',
  destructive: 'toast.error',
  warning: 'toast.warning',
  info: 'toast.info',
  default: 'toast',
};

function convertFile(content) {
  const lines = content.split('\n');
  const result = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Detecta início de um bloco toast({ que ainda não foi convertido
    const isToastBlock = /^\s*toast\(\{/.test(line) &&
      !line.includes('toast.success') &&
      !line.includes('toast.error') &&
      !line.includes('toast.warning') &&
      !line.includes('toast.info');

    if (isToastBlock) {
      const indent = line.match(/^(\s*)/)[1];
      const blockLines = [line];
      let j = i + 1;

      // Coleta linhas do bloco até encontrar o fechamento });
      while (j < lines.length) {
        blockLines.push(lines[j]);
        if (lines[j].trim().match(/^\}\);?\s*$/)) {
          j++;
          break;
        }
        j++;
      }

      const block = blockLines.join('\n');

      // Extrai title (valor entre aspas simples/duplas ou template literal)
      const titleMatch = block.match(/title:\s*(`[^`]*`|"[^"]*"|'[^']*')/);
      // Extrai description - pode ser qualquer expressão até a vírgula ou fechamento
      const descMatch = block.match(/description:\s*([\s\S]*?)(?:,\s*(?:variant|title)\s*:|,?\s*\}\))/);
      // Extrai variant
      const variantMatch = block.match(/variant:\s*"([^"]+)"/);

      if (titleMatch) {
        const title = titleMatch[1];
        const variant = variantMatch ? variantMatch[1] : 'default';
        const fn = variantMap[variant] || 'toast';

        if (descMatch) {
          const desc = descMatch[1].trim().replace(/,\s*$/, '').trim();
          result.push(`${indent}${fn}(${title}, {`);
          result.push(`${indent}  description: ${desc},`);
          result.push(`${indent}});`);
        } else {
          result.push(`${indent}${fn}(${title});`);
        }

        i = j;
        continue;
      }
    }

    result.push(line);
    i++;
  }

  return result.join('\n');
}

for (const file of files) {
  try {
    const content = readFileSync(file, 'utf8');
    const converted = convertFile(content);
    if (content !== converted) {
      writeFileSync(file, converted, 'utf8');
      console.log(`✅ Converted: ${file.split('/').slice(-2).join('/')}`);
    } else {
      console.log(`⏭️  No changes: ${file.split('/').slice(-2).join('/')}`);
    }
  } catch (err) {
    console.error(`❌ Error: ${file}`, err.message);
  }
}

console.log('\nDone!');
