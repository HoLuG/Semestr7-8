param(
  [string]$InputDoc = $(Get-ChildItem -LiteralPath . -Filter *.doc | Select-Object -First 1 | ForEach-Object FullName),
  [string]$OutputTxt = $null,
  [switch]$AlsoPdf
)

if (-not $InputDoc) {
  throw "No .doc file found in current directory."
}

if (-not $OutputTxt) {
  $OutputTxt = [System.IO.Path]::ChangeExtension($InputDoc, "txt")
}

$outputPdf = [System.IO.Path]::ChangeExtension($InputDoc, "pdf")

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
  $doc = $word.Documents.Open($InputDoc, $false, $true)
  # 2 = wdFormatText
  $doc.SaveAs([ref]$OutputTxt, [ref]2)

  if ($AlsoPdf) {
    # 17 = wdFormatPDF
    $doc.SaveAs([ref]$outputPdf, [ref]17)
  }
  $doc.Close()
}
finally {
  $word.Quit()
}

Write-Output $OutputTxt
