# Script to move remaining templates with subdirectories

$globalTemplatesPath = "c:\Users\Admin\OneDrive\Desktop\logisEdge\templates"
$projectRoot = "c:\Users\Admin\OneDrive\Desktop\logisEdge"

# Function to copy directory recursively
function Copy-DirectoryRecursive {
    param(
        [string]$Source,
        [string]$Destination
    )
    
    if (!(Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    
    Get-ChildItem -Path $Source -Recurse | ForEach-Object {
        $targetPath = $_.FullName.Replace($Source, $Destination)
        
        if ($_.PSIsContainer) {
            if (!(Test-Path $targetPath)) {
                New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
            }
        } else {
            $targetDir = Split-Path $targetPath -Parent
            if (!(Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item -Path $_.FullName -Destination $targetPath -Force
            Write-Host "Copied: $($_.FullName) to $targetPath"
        }
    }
}

# Apps to process
$remainingApps = @('data_cleaning_tool', 'documentation', 'grn', 'invoice')

foreach ($appName in $remainingApps) {
    $sourceDir = Join-Path $globalTemplatesPath $appName
    $targetAppDir = Join-Path $projectRoot $appName
    
    if ((Test-Path $sourceDir) -and (Test-Path $targetAppDir)) {
        $targetTemplatesDir = Join-Path $targetAppDir "templates\$appName"
        
        Write-Host "Processing $appName..."
        Copy-DirectoryRecursive -Source $sourceDir -Destination $targetTemplatesDir
        
        # Remove source directory after copying
        Remove-Item -Path $sourceDir -Recurse -Force
        Write-Host "Removed source directory: $sourceDir"
    }
}

Write-Host "Remaining template migration completed!"