import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/acer/Downloads/template_import_aset_kib_20260826 (1).xlsx";
const outputDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "outputs", "asset_import_fix_20260826");
const outputPath = path.join(outputDir, "template_import_aset_kib_20260826_fixed.xlsx");
const previewPath = path.join(outputDir, "Lembar1_fixed.png");

await fs.mkdir(outputDir, { recursive: true });
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const sheet = workbook.worksheets.getItemAt(0);
const used = sheet.getUsedRange(false);
if (!used) throw new Error("Workbook tidak memiliki area data.");

const values = used.values;
const columnCount = values[0]?.length ?? 0;
const dataStartIndex = 6; // Excel row 7, as stated by the template.
const headers = values[5] ?? [];
const headerIndex = Object.fromEntries(headers.map((header, index) => [header, index]));
const serialIndex = headerIndex["Nomor Seri"];
if (serialIndex === undefined) throw new Error("Header Nomor Seri tidak ditemukan pada template.");
const originalDataRows = values.slice(dataStartIndex);
const nonEmptyRows = originalDataRows.filter(row => row.some(value => value !== null && value !== undefined && value !== ""));
const keptRows = nonEmptyRows.filter(row => {
  const assetName = String(row[9] ?? "").trim().toUpperCase(); // J: Nama Aset
  return !assetName.startsWith("CONTOH");
});
const removedSampleCount = nonEmptyRows.length - keptRows.length;

for (const [offset, row] of keptRows.entries()) {
  const serial = String(row[serialIndex] ?? "").trim();
  if (!serial) throw new Error(`Nomor Seri kosong pada baris data ke-${offset + 7}; tidak boleh diisi dengan data rekaan.`);
  row[serialIndex] = serial;
}

if (keptRows.length > 0) {
  sheet.getRangeByIndexes(dataStartIndex, 0, keptRows.length, columnCount).values = keptRows;
  // Serial numbers are identifiers: write them explicitly as text so the web importer cannot drop them.
  sheet.getRangeByIndexes(dataStartIndex, serialIndex, keptRows.length, 1).values = keptRows.map(row => [String(row[serialIndex])]);
  sheet.getRangeByIndexes(dataStartIndex, serialIndex, keptRows.length, 1).format.numberFormat = "@";
}

// Compatibility alias for the web screen that labels this field "No Seri".
// Keep the official template column "Nomor Seri" unchanged and do not shift any KIB columns.
const aliasIndex = columnCount;
sheet.getRangeByIndexes(5, aliasIndex, 1, 1).copyFrom(sheet.getRangeByIndexes(5, serialIndex, 1, 1), "all");
sheet.getRangeByIndexes(5, aliasIndex, 1, 1).values = [["No Seri"]];
if (keptRows.length > 0) {
  sheet.getRangeByIndexes(dataStartIndex, aliasIndex, keptRows.length, 1).copyFrom(
    sheet.getRangeByIndexes(dataStartIndex, serialIndex, keptRows.length, 1),
    "all",
  );
  sheet.getRangeByIndexes(dataStartIndex, aliasIndex, keptRows.length, 1).values = keptRows.map(row => [String(row[serialIndex])]);
  sheet.getRangeByIndexes(dataStartIndex, aliasIndex, keptRows.length, 1).format.numberFormat = "@";
}

const rowsToClear = nonEmptyRows.length - keptRows.length;
if (rowsToClear > 0) {
  sheet.getRangeByIndexes(dataStartIndex + keptRows.length, 0, rowsToClear, columnCount).clear({ applyTo: "all" });
}

const remaining = sheet.getUsedRange(false);
const requiredHeaders = ["Kode Level 1", "Nama Aset", "Spesifikasi", "Nomor Seri", "Jumlah"];
const validation = keptRows.map((row, offset) => ({
  row: offset + 7,
  missing: requiredHeaders.filter(header => row[headerIndex[header]] === null || row[headerIndex[header]] === undefined || String(row[headerIndex[header]]).trim() === ""),
  serial: String(row[serialIndex]),
}));
if (validation.some(item => item.missing.length > 0 || !item.serial)) throw new Error(`Validasi kolom wajib gagal: ${JSON.stringify(validation)}`);
const check = await workbook.inspect({
  kind: "table",
  sheetId: sheet.name,
  range: "A6:AT10",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 45,
  tableMaxCellChars: 100,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(`REMOVED_SAMPLE_ROWS:${removedSampleCount}`);
console.log(`REMAINING_USED_RANGE:${remaining?.address ?? "none"}`);
console.log(`CHECK:${check.ndjson}`);
console.log(`ERRORS:${errors.ndjson}`);

const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 2, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`OUTPUT:${outputPath}`);
