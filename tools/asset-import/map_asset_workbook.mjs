import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/acer/Downloads/template_import_aset_kib_20260826 (1).xlsx";
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const ws = wb.worksheets.getItemAt(0);
const used = ws.getUsedRange(false);
const headers = used.values[5];
const rowNumbers = [6,7];
for (const r of rowNumbers) {
  const vals = used.values[r] ?? [];
  console.log(`ROW${r+1}`);
  for (let c=0; c<headers.length; c++) {
    const value = vals[c];
    if (value !== null && value !== undefined && value !== "") console.log(`${c+1}\t${headers[c]}\t${JSON.stringify(value)}`);
  }
}
console.log("USED", used.address, "ROWS", used.values.length, "COLS", headers.length);
console.log("TABLES", ws.tables.items.length);
console.log("WIDTHS", JSON.stringify(headers.map((_,i)=>ws.getRangeByIndexes(0,i,1,1).format.columnWidth)));
console.log("ROWHEIGHTS", JSON.stringify([1,2,4,6,7,8].map(r=>ws.getRange(`A${r}`).format.rowHeight)));
