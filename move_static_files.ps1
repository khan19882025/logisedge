# Script to move static files from global static directory to app-specific directories

$globalStaticPath = "c:\Users\Admin\OneDrive\Desktop\logisEdge\static"
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
            Write-Host "Copied: $($_.Name) to $($targetPath.Replace($projectRoot, ''))"
        }
    }
}

# Get all app-specific directories in the global static folder
Get-ChildItem -Path $globalStaticPath -Directory | ForEach-Object {
    $appName = $_.Name
    $sourceDir = $_.FullName
    $targetAppDir = Join-Path $projectRoot $appName
    
    # Skip common directories that should remain global
    $skipDirs = @('css', 'js', 'img', 'fonts')
    if ($appName -in $skipDirs) {
        Write-Host "Skipping global directory: $appName"
        return
    }
    
    # Check if the app directory exists
    if (Test-Path $targetAppDir) {
        $targetStaticDir = Join-Path $targetAppDir "static\$appName"
        
        Write-Host "Processing static files for $appName..."
        Copy-DirectoryRecursive -Source $sourceDir -Destination $targetStaticDir
        
        # Remove source directory after copying
        Remove-Item -Path $sourceDir -Recurse -Force
        Write-Host "Removed source directory: $sourceDir"
    } else {
        Write-Host "Warning: App directory does not exist for $appName"
    }
}

# Handle files in css subdirectories that belong to specific apps
$cssDir = Join-Path $globalStaticPath "css"
if (Test-Path $cssDir) {
    Get-ChildItem -Path $cssDir -Directory | ForEach-Object {
        $appName = $_.Name
        $sourceDir = $_.FullName
        $targetAppDir = Join-Path $projectRoot $appName
        
        if (Test-Path $targetAppDir) {
            $targetStaticDir = Join-Path $targetAppDir "static\$appName\css"
            
            Write-Host "Processing CSS files for $appName..."
            Copy-DirectoryRecursive -Source $sourceDir -Destination $targetStaticDir
            
            # Remove source directory after copying
            Remove-Item -Path $sourceDir -Recurse -Force
            Write-Host "Removed CSS source directory: $sourceDir"
        }
    }
}

# Handle files in js subdirectories that belong to specific apps
$jsDir = Join-Path $globalStaticPath "js"
if (Test-Path $jsDir) {
    Get-ChildItem -Path $jsDir -Directory | ForEach-Object {
        $appName = $_.Name
        $sourceDir = $_.FullName
        $targetAppDir = Join-Path $projectRoot $appName
        
        if (Test-Path $targetAppDir) {
            $targetStaticDir = Join-Path $targetAppDir "static\$appName\js"
            
            Write-Host "Processing JS files for $appName..."
            Copy-DirectoryRecursive -Source $sourceDir -Destination $targetStaticDir
            
            # Remove source directory after copying
            Remove-Item -Path $sourceDir -Recurse -Force
            Write-Host "Removed JS source directory: $sourceDir"
        }
    }
}

Write-Host "Static files migration completed!"