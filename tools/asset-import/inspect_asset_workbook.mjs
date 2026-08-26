import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/acer/Downloads/template_import_aset_kib_20260826 (1).xlsx";
const outDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "workbook_inspection");
await fs.mkdir(outDir, { recursive: true });

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const summary = await workbook.inspect({
  kind: "workbook,sheet,table,region,computedStyle,definedName,drawing",
  maxChars: 20000,
  tableMaxRows: 20,
  tableMaxCols: 30,
  tableMaxCellChars: 200,
});
console.log(summary.ndjson);

const sheets = workbook.worksheets.items;
for (const sheet of sheets) {
  console.log(`SHEET:${sheet.name}`);
  const used = sheet.getUsedRange(false);
  if (used) {
    console.log("USED_VALUES", JSON.stringify(used.values));
    console.log("USED_FORMULAS", JSON.stringify(used.formulas));
    console.log("USED_DISPLAY_FORMULAS", JSON.stringify(used.displayFormulas));
    const style = await workbook.inspect({
      kind: "computedStyle",
      sheetId: sheet.name,
      range: used.address,
      maxChars: 12000,
    });
    console.log("STYLES", style.ndjson);
    const preview = await workbook.render({
      sheetName: sheet.name,
      autoCrop: "all",
      scale: 2,
      format: "png",
    });
    await fs.writeFile(path.join(outDir, `${sheet.name.replace(/[^a-z0-9_-]/gi, "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "formula error scan",
});
console.log("ERRORS", errors.ndjson);
