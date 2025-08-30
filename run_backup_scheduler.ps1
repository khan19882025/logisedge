# LogisEdge Backup Scheduler PowerShell Script
# This script can be used with Windows Task Scheduler

param(
    [switch]$Force,
    [string]$LogFile = "C:\backups\logisEdge\backup_scheduler.log"
)

# Set execution policy for this session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Create log directory if it doesn't exist
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Function to write to log
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Start logging
Write-Log "Starting LogisEdge Backup Scheduler"
Write-Log "Working Directory: $(Get-Location)"
Write-Log "Python Version: $(python --version 2>&1)"

# Change to project directory
$ProjectDir = "C:\Users\Admin\OneDrive\Desktop\logisEdge"
if (Test-Path $ProjectDir) {
    Set-Location $ProjectDir
    Write-Log "Changed to project directory: $ProjectDir"
} else {
    Write-Log "ERROR: Project directory not found: $ProjectDir" "ERROR"
    exit 1
}

# Build command
$Command = "python manage.py run_scheduled_backups"
if ($Force) {
    $Command += " --force"
    Write-Log "Force mode enabled"
}

# Run backup scheduler
Write-Log "Executing: $Command"
try {
    $Result = Invoke-Expression $Command 2>&1
    $ExitCode = $LASTEXITCODE
    
    if ($ExitCode -eq 0) {
        Write-Log "Backup scheduler completed successfully"
        foreach ($Line in $Result) {
            Write-Log $Line
        }
    } else {
        Write-Log "Backup scheduler failed with exit code: $ExitCode" "ERROR"
        foreach ($Line in $Result) {
            Write-Log $Line "ERROR"
        }
    }
} catch {
    Write-Log "Exception occurred: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Log "Backup scheduler script completed"
exit $ExitCode
