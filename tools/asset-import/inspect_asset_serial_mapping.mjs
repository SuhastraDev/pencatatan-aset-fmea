import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const paths = [
  path.join(toolDir, "outputs", "asset_import_fix_20260826", "template_import_aset_kib_20260826_fixed.xlsx"),
  "C:/Users/acer/Downloads/template_import_aset_kib_20260826 (1).xlsx",
];

for (const path of paths) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const ws = wb.worksheets.getItemAt(0);
  const used = ws.getUsedRange(false);
  const vals = used?.values ?? [];
  const headers = vals[5] ?? [];
  const row = vals[6] ?? [];
  console.log(`FILE:${path}`);
  console.log("USED", used?.address);
  for (let i=0; i<headers.length; i++) {
    if (["Nama Aset","Merk","Type","Spesifikasi","Merk/Type","Nomor Seri","Jumlah","Satuan","Nama Ruangan","Kondisi","Status"].includes(headers[i])) {
      console.log(`${i+1}\t${headers[i]}\t${JSON.stringify(row[i])}\tformula=${JSON.stringify(used?.formulas?.[6]?.[i] ?? "")}`);
    }
  }
  const style = await wb.inspect({kind:"computedStyle", sheetId:ws.name, range:"AB6:AE7", maxChars:4000});
  console.log("STYLE", style.ndjson);
}
