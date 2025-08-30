# Script to move templates from global templates directory to app-specific directories

$globalTemplatesPath = "c:\Users\Admin\OneDrive\Desktop\logisEdge\templates"
$projectRoot = "c:\Users\Admin\OneDrive\Desktop\logisEdge"

# Get all subdirectories in the global templates folder (excluding base.html)
Get-ChildItem -Path $globalTemplatesPath -Directory | ForEach-Object {
    $appName = $_.Name
    $sourceDir = $_.FullName
    $targetAppDir = Join-Path $projectRoot $appName
    
    # Check if the app directory exists
    if (Test-Path $targetAppDir) {
        $targetTemplatesDir = Join-Path $targetAppDir "templates\$appName"
        
        # Ensure the target templates directory exists
        if (!(Test-Path $targetTemplatesDir)) {
            New-Item -ItemType Directory -Path $targetTemplatesDir -Force | Out-Null
        }
        
        # Move all files from source to target
        try {
            Get-ChildItem -Path $sourceDir -File -Recurse | ForEach-Object {
                $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
                $targetFile = Join-Path $targetTemplatesDir $relativePath
                $targetFileDir = Split-Path $targetFile -Parent
                
                # Create target directory if it doesn't exist
                if (!(Test-Path $targetFileDir)) {
                    New-Item -ItemType Directory -Path $targetFileDir -Force | Out-Null
                }
                
                # Move the file
                Move-Item -Path $_.FullName -Destination $targetFile -Force
                Write-Host "Moved: $($_.Name) to $appName/templates/$appName/"
            }
            
            # Remove empty source directory
            if ((Get-ChildItem -Path $sourceDir -Recurse | Measure-Object).Count -eq 0) {
                Remove-Item -Path $sourceDir -Recurse -Force
                Write-Host "Removed empty directory: $sourceDir"
            }
        }
        catch {
            Write-Host "Error moving templates for $appName : $($_.Exception.Message)"
        }
    } else {
        Write-Host "Warning: App directory does not exist for $appName"
    }
}

Write-Host "Template migration completed!"