# =========================
# build_app.ps1 — PyInstaller + Realtime 60fps ASCII animation + Bottom Progress
# Compatible: PowerShell 5.1 / 7+
# =========================

# 1) Console UTF-8 (best effort)
try { chcp 65001 | Out-Null } catch {}
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}
try { [Console]::InputEncoding  = [System.Text.UTF8Encoding]::new() } catch {}

# 2) App config
$MAIN_SCRIPT = "main.py"
$APP_ICON    = "app/assets/icons/app_icon.ico"
$DATA_DIR    = "app/data"
$APP_NAME    = "ProductManagementApp"

# 3) PyInstaller args
$pyinstallerArgs = @(
  "--name", $APP_NAME,
  "--onefile",
  "--windowed",
  "--add-data", "$DATA_DIR/products.json;.",
  "--add-data", "$DATA_DIR/carts.json;.",
  "--add-data", "$DATA_DIR/categories.json;.",
  "--add-data", "$DATA_DIR/customers.json;.",
  "--add-data", "$DATA_DIR/orders.json;.",
  "--add-data", "$DATA_DIR/users.json;.",
  "--icon", $APP_ICON,
  $MAIN_SCRIPT
)

# 4) Lock buffer height = window height (avoid scroll)
try {
  $raw = $Host.UI.RawUI
  $ws = $raw.WindowSize
  $bs = $raw.BufferSize
  if ($bs.Height -ne $ws.Height) {
    $raw.BufferSize = New-Object System.Management.Automation.Host.Size($bs.Width, $ws.Height)
  }
} catch {}

# 5) ANSI helpers (safe fallbacks)
$Esc = [char]27
function Ansi([string]$code) { return "$Esc[$code" + "m" }
$CLR = @{
  green   = (Ansi "32")
  red     = (Ansi "31")
  yellow  = (Ansi "33")
  blue    = (Ansi "34")
  magenta = (Ansi "35")
  cyan    = (Ansi "36")
  bold    = (Ansi "1")
  reset   = (Ansi "0")
}
function ColorWrap([string]$s,[string]$c) { return $CLR[$c] + $s + $CLR.reset }

# 6) Console utilities
function Get-ConsoleSize {
  try { return @{ W=[Console]::WindowWidth; H=[Console]::WindowHeight } }
  catch { return @{ W=120; H=30 } }
}
function Write-Fixed([int]$row, [string]$text) {
  $s = Get-ConsoleSize
  $t = $text
  if ($t.Length -gt ($s.W - 1)) { $t = $t.Substring(0, $s.W - 1) }
  [Console]::CursorVisible = $false
  [Console]::SetCursorPosition(0, [Math]::Max(0,$row))
  $pad = " " * ([Math]::Max(0, $s.W - $t.Length - 1))
  Write-Host -NoNewline ($t + $pad)
}
function Clear-Region([int]$top, [int]$bottom) {
  $s = Get-ConsoleSize
  for ($r=$top; $r -le $bottom; $r++) { Write-Fixed $r "" }
}

# 7) Bottom progress renderer (ASCII only)
# Bar chars use only ASCII to avoid encoding issues
function Render-Progress([int]$percent, [string]$status, [TimeSpan]$elapsed) {
  $s = Get-ConsoleSize
  $rowProgress = $s.H - 1
  $rowStatus   = $s.H - 2

  $p = [Math]::Max(0,[Math]::Min(100,$percent))
  $elapsedStr = [string]::Format("{0:mm\:ss}", $elapsed)

  $prefix = $CLR.bold + $CLR.cyan + $status + $CLR.reset
  $right  = $CLR.yellow + $elapsedStr + $CLR.reset

  $minBar = 20
  $spaceForBar = $s.W - ($prefix.Length + $right.Length + 8)
  $barW = [Math]::Max($minBar, $spaceForBar)

  $filled = [int]([math]::Round($p/100 * $barW))
  if ($filled -lt 0) { $filled = 0 }
  if ($filled -gt $barW) { $filled = $barW }

  $bar = $CLR.green + ("#" * $filled) + $CLR.blue + ("-" * ($barW - $filled)) + $CLR.reset
  Write-Fixed $rowStatus (ColorWrap("PyInstaller is packaging...", "magenta"))
  Write-Fixed $rowProgress ("$prefix $bar $p% $right")
}

# 8) 60fps Cube ASCII frames (pure ASCII, no accents)
$cubes = @(
@"
   ________
  /|      /|
 / | hoan/ |
+--+----+  |
|  |tq03|  |
|  +----+--+
| /      | /
|/_______|/
"@,
@"
   ________
  /      /|
 / hoan / |
+----+ +  |
|tq03| |  |
|----+ +--+
|      / /
|______/ /
"@,
@"
   ________
  |\      \
  | \ hoan \
  |  +----++
  |  |tq03| |
  +--+----+ |
   \      \ |
    \______\|
"@,
@"
   ________
  |\      \
  | \      \
  |  +----+ \
  |  |hoan|  \
  +--+tq03+--+
   \  ----\  |
    \      \ |
     \______\|
"@
)

function Render-Cube([int]$frame) {
  $s = Get-ConsoleSize
  # Reserve 2 lines for status+progress
  $top = [Math]::Max(0, $s.H - 2 - 8) # 8 lines height of the cube block
  $art = $cubes[$frame % $cubes.Count] -split "`r?`n"
  for ($i=0; $i -lt $art.Count; $i++) {
    $line = $art[$i]
    if ($line.Length -gt ($s.W - 1)) { $line = $line.Substring(0, $s.W - 1) }
    Write-Fixed ($top + $i) $line
  }
}

# 9) Start PyInstaller process
Write-Host "Starting package: $APP_NAME"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = "pyinstaller"
$psi.Arguments = ($pyinstallerArgs -join " ")
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)

# Prepare logs
$sbOut = [System.Text.StringBuilder]::new()
$sbErr = [System.Text.StringBuilder]::new()

# 10) Main loop — target 60fps
$frame = 0
$progress = 0
# target frame interval ~16ms
$targetMs = 16
$lastTick = [Environment]::TickCount

# Pre-clear visual area (cube + status + progress)
$s = Get-ConsoleSize
Clear-Region ([Math]::Max(0, $s.H-12)) ($s.H-1)

while (-not $proc.HasExited) {
  # Read stdout/stderr in small batches to avoid blocking
  for ($k=0; $k -lt 120 -and -not $proc.StandardOutput.EndOfStream; $k++) {
    [void]$sbOut.AppendLine($proc.StandardOutput.ReadLine())
  }
  for ($k=0; $k -lt 120 -and -not $proc.StandardError.EndOfStream; $k++) {
    [void]$sbErr.AppendLine($proc.StandardError.ReadLine())
  }

  # Render (if enough time passed to target 60fps)
  $now = [Environment]::TickCount
  $delta = $now - $lastTick
  if ($delta -ge $targetMs) {
    $lastTick = $now
    Render-Cube $frame
    $frame++

    # Time-based progress up to 97%
    $target = [int][Math]::Min(97, $sw.Elapsed.TotalSeconds * 9.0)  # ~11s -> 97%
    if ($target -gt $progress) { $progress = $target }
    Render-Progress $progress "Packaging:" $sw.Elapsed
  }

  # Short sleep to give CPU breath; 0-5ms depending on delta
  Start-Sleep -Milliseconds 5
}

# Flush remaining logs
while (-not $proc.StandardOutput.EndOfStream) { [void]$sbOut.AppendLine($proc.StandardOutput.ReadLine()) }
while (-not $proc.StandardError.EndOfStream)  { [void]$sbErr.AppendLine($proc.StandardError.ReadLine()) }

# Save logs UTF-8 BOM
$utf8bom = New-Object System.Text.UTF8Encoding($true)
[IO.File]::WriteAllText("build_stdout.log", $sbOut.ToString(), $utf8bom)
[IO.File]::WriteAllText("build_stderr.log", $sbErr.ToString(), $utf8bom)

# Final visuals
Render-Cube $frame
Render-Progress 100 "Done:" $sw.Elapsed
[Console]::CursorVisible = $true

# 11) Report result
if ($proc.ExitCode -eq 0) {
  Write-Host ""
  Write-Host ($CLR.green + "Success!" + $CLR.reset + " Executable in 'dist/'.")
  Write-Host ("File: dist/" + $APP_NAME + ".exe")
} else {
  Write-Host ""
  Write-Host ($CLR.red + "Failed." + $CLR.reset + " ExitCode: " + $proc.ExitCode)
  Write-Host "See: build_stdout.log, build_stderr.log"
}
Write-Host "Finished."
