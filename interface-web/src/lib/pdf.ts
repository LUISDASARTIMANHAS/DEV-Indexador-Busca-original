const normalizePdfText = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\x20-\x7E]/g, " ");

const escapePdfText = (value: string) =>
  normalizePdfText(value).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");

export const buildTextPdfBlob = (lines: string[]) => {
  const pageLines: string[][] = [];
  for (let index = 0; index < lines.length; index += 46) {
    pageLines.push(lines.slice(index, index + 46));
  }
  if (pageLines.length === 0) {
    pageLines.push([""]);
  }

  const fontObjectNumber = 3 + (pageLines.length * 2);
  const pageObjectNumbers = pageLines.map((_, index) => 3 + (index * 2));
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    `<< /Type /Pages /Kids [${pageObjectNumbers.map((number) => `${number} 0 R`).join(" ")}] /Count ${pageLines.length} >>`,
  ];
  pageLines.forEach((page, pageIndex) => {
    const pageObjectNumber = pageObjectNumbers[pageIndex];
    const contentObjectNumber = pageObjectNumber + 1;
    const stream = page.map((line, lineIndex) => {
      const yPosition = 800 - (lineIndex * 16);
      return `BT /F1 10 Tf 48 ${yPosition} Td (${escapePdfText(line).slice(0, 104)}) Tj ET`;
    }).join("\n");
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${fontObjectNumber} 0 R >> >> /Contents ${contentObjectNumber} 0 R >>`,
      `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    );
  });
  objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");

  let output = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(output.length);
    output += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xrefOffset = output.length;
  output += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  offsets.slice(1).forEach((offset) => {
    output += `${String(offset).padStart(10, "0")} 00000 n \n`;
  });
  output += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

  return new Blob([output], { type: "application/pdf" });
};
