# NOT READY

$configs = @()

foreach ($m in 19,46,64,256,1024,2048) {
    foreach ($t in 1,2,3) {
        foreach ($p in 1,4) {
            $configs += [PSCustomObject]@{
                Label = "Argon2id m=${m}MiB t=$t p=$p"
                Mode  = 34000
                File  = "hash_argon2_m${m}_t${t}_p${p}.txt"
            }
        }
    }
}
foreach ($it in 100000,600000) {
    $configs += [PSCustomObject]@{
        Label = "PBKDF2-HMAC-SHA256 it=$it"
        Mode  = 10900
        File  = "hash_pbkdf2_hashcat_it${it}.txt"
    }
}
foreach ($c in 10,12,14) {
    $configs += [PSCustomObject]@{
        Label = "bcrypt cost=$c"
        Mode  = 3200
        File  = "hash_bcrypt_c${c}.txt"
    }
}

$results = @()
$i = 0
foreach ($cfg in $configs) {
    $i++
    Write-Host "[$i/$($configs.Count)] $($cfg.Label)"

    $output = & .\hashcat.exe -m $cfg.Mode -a 0 -D 1 --potfile-disable `
        --runtime=20 --status --status-timer=5 $cfg.File rockyou.txt 2>&1

    $speedMatches = $output | Select-String -Pattern 'Speed\.#\d+\.*:\s+([\d.,]+)\s*(H/s|kH/s|MH/s|GH/s)'
    $hps = $null
    if ($speedMatches.Count -gt 0) {
        $last = $speedMatches[$speedMatches.Count - 1]
        $value = [double]($last.Matches[0].Groups[1].Value -replace ',', '')
        $unit = $last.Matches[0].Groups[2].Value
        $mult = switch ($unit) {
            'H/s'  { 1 }
            'kH/s' { 1000 }
            'MH/s' { 1000000 }
            'GH/s' { 1000000000 }
        }
        $hps = $value * $mult
    } else {
        Write-Host "  WARNING: could not parse a speed line for $($cfg.Label)"
    }

    $results += [PSCustomObject]@{
        Label    = $cfg.Label
        Mode     = $cfg.Mode
        File     = $cfg.File
        Speed_Hs = $hps
    }
}

$ts = Get-Date -Format "yyyyMMddTHHmmss"
$outFile = "hashcat_sweep_run_$ts.csv"
$results | Export-Csv -Path $outFile -NoTypeInformation -Encoding ascii
Write-Host ""
Write-Host "Saved $($results.Count) results to $outFile"
