# Ensure arguments are provided
if ($args.Count -eq 0) {
    Write-Host "Error: No arguments provided."
    Write-Host "Usage:"
    Write-Host "run.ps1 -t <tag> OR -m <map1> <map2> ..."
    exit 1
}

# Check if the first argument is -t or -m
$flag = $args[0]

if ($flag -eq "-t") {
    # Ensure a tag argument is provided
    if ($args.Count -ne 2) {
        Write-Host "Error: Missing tag argument."
        Write-Host "Usage:"
        Write-Host "run.ps1 -t <tag>"
        exit 1
    }

    # Retrieve the tag argument
    $Tag = $args[1]
    Write-Host "Processing tag: $Tag"

    # Fetch the maps for the specified tag and save them to a file
    python atlasMaps.py $Tag > maps.txt

    # Read the maps from the file as an array
    $maps = Get-Content maps.txt
    if ($maps.Count -eq 0) {
        Write-Host "Error: No maps found for the given tag."
        exit 1
    }

    # Debug: Print the list of maps
    Write-Host "Maps to be processed: $maps"

    # Pass the array of maps directly to Python
    python numSSes.py @maps > output.txt

    # Extract and display the result
    $finalResult = Get-Content output.txt | Select-String -Pattern "Number of SSes" | Select-Object -Last 1
    $finalText = $finalResult -replace "Number of SSes:", "Number of SSes under tag:"
    Write-Host $finalText

} elseif ($flag -eq "-m") {
    # Ensure map arguments are provided
    if ($args.Count -le 1) {
        Write-Host "Error: Missing map arguments."
        Write-Host "Usage:"
        Write-Host "run.ps1 -m <map1> <map2> ..."
        exit 1
    }

    # Retrieve the map arguments (skip the flag itself)
    $Map = $args[1..$args.Count]
    Write-Host "Processing maps: $Map"

    # Pass the array of maps directly to Python
    python numSSes.py @Map > output.txt

    # Extract and display the result
    $finalResult = Get-Content output.txt | Select-String -Pattern "Number of SSes" | Select-Object -Last 1
    $finalText = $finalResult -replace "Number of SSes:", "Number of SSes under map:"
    Write-Host $finalText

} else {
    # Invalid flag provided
    Write-Host "Error: Invalid flag provided. Use -t for tag or -m for map."
    Write-Host "Usage:"
    Write-Host "run.ps1 -t <tag> OR -m <map1> <map2> ..."
    exit 1
}