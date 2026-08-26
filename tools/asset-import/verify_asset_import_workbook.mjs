import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const outputPath = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "outputs",
  "asset_import_fix_20260826",
  "template_import_aset_kib_20260826_fixed.xlsx",
);
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const ws = wb.worksheets.getItemAt(0);
const used = ws.getUsedRange(false);
const values = used?.values ?? [];
const headers = values[5] ?? [];
const rows = values.slice(6).filter(row => row.some(value => value !== null && value !== undefined && value !== ""));
const index = Object.fromEntries(headers.map((h, i) => [h, i]));
const required = ["Kode Level 1", "Nama Aset", "Spesifikasi", "Nomor Seri", "No Seri", "Jumlah"];
const checks = rows.map((row, n) => ({
  row: n + 7,
  isSample: String(row[index["Nama Aset"]] ?? "").trim().toUpperCase().startsWith("CONTOH"),
  missingRequired: required.filter(h => row[index[h]] === null || row[index[h]] === undefined || row[index[h]] === ""),
  name: row[index["Nama Aset"]],
  specification: row[index["Spesifikasi"]],
  serial: row[index["Nomor Seri"]],
  serialAlias: row[index["No Seri"]],
  quantity: row[index["Jumlah"]],
  levelCodes: headers.filter(h => h.startsWith("Kode Level")).map(h => row[index[h]]),
}));
const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "verification formula error scan",
});
console.log(JSON.stringify({usedRange: used?.address, rowCount: rows.length, checks, formulaErrors: errors.ndjson}, null, 2));
