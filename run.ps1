# Ensure arguments are provided
if ($args.Count -eq 0) {
    Write-Host "Error: No arguments provided."
    Write-Host "Usage:"
    Write-Host "run.ps1 [-t <tag>] [-m <map1> <map2> ...] [-force]"
    exit 1
}

# Initialize variables
$Tag = $null
$Maps = @()
$Force = $false  # Default value for Force

# Parse arguments
for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "-t" {
            # Process the tag flag
            if ($i + 1 -lt $args.Count) {
                $Tag = $args[$i + 1]
                $i++
            } else {
                Write-Host "Error: Missing value for -t flag."
                exit 1
            }
        }
        "-m" {
            # Process the maps flag
            if ($i + 1 -lt $args.Count) {
                $Maps = $args[($i + 1)..($args.Count - 1)]
                $i = $args.Count - 1
            } else {
                Write-Host "Error: Missing value for -m flag."
                exit 1
            }
        }
        "-force" {
            # Enable the force flag
            $Force = $true
        }
    }
}

# Ensure $Tag or $Maps is set
if (-not $Tag -and $Maps.Count -eq 0) {
    Write-Host "Error: You must specify either -t <tag> or -m <map1> <map2> ..."
    exit 1
}

# Logic for -t (tag mode)
if ($Tag) {
    Write-Host "Processing tag: $Tag"

    # Check if the tag file exists
    $tagFile = "./$Tag.txt"
    if (($Force -eq $false) -and (Test-Path $tagFile)) {
        Write-Host "Using cached map list from file: $tagFile"
    } else {
        Write-Host "Querying atlas for maps under tag: $Tag"
        python atlasMaps.py $Tag > $tagFile

        # Check if the file is empty or the list of maps is empty
        if ((Test-Path $tagFile) -and ((Get-Content $tagFile).Count -eq 0)) {
            Write-Host "No maps were found for tag: $Tag. Deleting empty cache file."
            Remove-Item $tagFile
        } elseif ((Test-Path $tagFile) -and ((Get-Item $tagFile).Length -eq 0)) {
            Write-Host "Cache file for tag $Tag has zero size. Deleting file."
            Remove-Item $tagFile
        }
    }

    # Read maps from the file if it exists
    if (Test-Path $tagFile) {
        $Maps = Get-Content $tagFile
    } else {
        Write-Host "Error: No maps found for the given tag and cache file was removed."
        exit 1
    }

    Write-Host "Maps to be processed: $Maps"
}

# Logic for -m (map mode)
if ($Maps.Count -gt 0) {
    Write-Host "Processing maps: $Maps"
    python numSSes.py @Maps > output.txt

    # Extract and display the result
    $finalResult = Get-Content output.txt | Select-String -Pattern "Number of SSes" | Select-Object -Last 1
    $finalText = $finalResult -replace "Number of SSes:", "Number of SSes:"
    Write-Host $finalText
}