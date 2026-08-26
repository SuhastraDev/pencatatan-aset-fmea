import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const paths = [
  "C:/Users/acer/Downloads/template_import_aset_kib_20260826.xlsx",
  "C:/Users/acer/Downloads/template_import_aset_kib_20260826 (1).xlsx",
  "C:/Users/acer/Downloads/template_import_aset_kib_20260818.xlsx",
];

for (const path of paths) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const sheet = wb.worksheets.getItemAt(0);
  const used = sheet.getUsedRange(false);
  console.log(`FILE:${path}`);
  console.log(`SHEET:${sheet.name} USED:${used?.address}`);
  console.log("VALUES", JSON.stringify(used?.values));
  console.log("TABLES", JSON.stringify(sheet.tables.items.map(t => ({name:t.name,address:t.range?.address,style:t.style}))));
  console.log("VALIDATIONS", JSON.stringify(sheet.dataValidations?.items ?? []));
}
