param(
    [string]$Manifest = (Join-Path $PSScriptRoot "manifest.json")
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

function Export-JpegVariant {
    param(
        [System.Drawing.Image]$Source,
        [string]$Destination,
        [int]$Width,
        [int]$Height,
        [long]$Quality
    )

    $directory = Split-Path -Parent $Destination
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null

    $bitmap = New-Object System.Drawing.Bitmap(
        $Width,
        $Height,
        [System.Drawing.Imaging.PixelFormat]::Format24bppRgb
    )
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    try {
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $graphics.DrawImage($Source, 0, 0, $Width, $Height)

        $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
            Where-Object MimeType -eq "image/jpeg" |
            Select-Object -First 1
        $qualityEncoder = [System.Drawing.Imaging.Encoder]::Quality
        $encoderParameters = New-Object System.Drawing.Imaging.EncoderParameters(1)
        $encoderParameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
            $qualityEncoder,
            $Quality
        )

        try {
            $bitmap.Save($Destination, $codec, $encoderParameters)
        } finally {
            $encoderParameters.Dispose()
        }
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$manifestPath = [System.IO.Path]::GetFullPath($Manifest)
$manifestDirectory = Split-Path -Parent $manifestPath
$catalog = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 |
    ConvertFrom-Json
$count = 0

foreach ($card in $catalog.cards) {
    foreach ($variant in $card.variants) {
        $sourcePath = [System.IO.Path]::GetFullPath(
            (Join-Path $manifestDirectory $variant.sourcePath)
        )
        $previewPath = [System.IO.Path]::GetFullPath(
            (Join-Path $manifestDirectory $variant.previewPath)
        )
        $microPath = [System.IO.Path]::GetFullPath(
            (Join-Path $manifestDirectory $variant.microPath)
        )
        $source = [System.Drawing.Image]::FromFile($sourcePath)

        try {
            Export-JpegVariant $source $previewPath 358 500 88
            Export-JpegVariant $source $microPath 20 20 85
        } finally {
            $source.Dispose()
        }

        $count++
    }
}

Write-Output "generated variants=$count images=$($count * 2)"
