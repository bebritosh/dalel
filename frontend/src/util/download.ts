// Save a Blob as a file. The anchor is attached to the DOM and the object URL
// is revoked later: revoking right after click() can cancel the download or
// leave a truncated file in some browsers (Word then reports unreadable content).
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
