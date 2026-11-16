# NOT READY

BASE=/mnt/c/hashcat/hashcat-7.1.2
WORDLIST=$BASE/rockyou.txt
TS=$(date +%Y%m%dT%H%M%S)
POT=$BASE/john_sweep_$TS.pot
OUT=john_sweep_run_$TS.csv

LABELS=()
FORMATS=()
FILES=()

for m in 19 46 64 256 1024 2048; do
    for t in 1 2 3; do
        for p in 1 4; do
            LABELS+=("Argon2id m=${m}MiB t=${t} p=${p}")
            FORMATS+=("argon2")
            FILES+=("hash_argon2_m${m}_t${t}_p${p}.txt")
        done
    done
done
for it in 100000 600000 1200000; do
    LABELS+=("PBKDF2-HMAC-SHA256 it=${it}")
    FORMATS+=("PBKDF2-HMAC-SHA256")
    FILES+=("hash_pbkdf2_john_it${it}.txt")
done
for c in 10 12 14; do
    LABELS+=("bcrypt cost=${c}")
    FORMATS+=("bcrypt")
    FILES+=("hash_bcrypt_c${c}.txt")
done

echo "label,format,file,speed_cs" > "$OUT"

N=${#LABELS[@]}
for i in "${!LABELS[@]}"; do
    label="${LABELS[$i]}"
    format="${FORMATS[$i]}"
    file="$BASE/${FILES[$i]}"
    echo "[$((i+1))/$N] $label"

    output=$(./john --format="$format" --pot="$POT" --max-run-time=20 \
        --progress-every=5 --wordlist="$WORDLIST" "$file" 2>&1)

    # Lowercase c/s is crypts/sec, which is what we want. Uppercase C/s
    # is a different, corrected figure -- grep here is case-sensitive
    # on purpose so it doesn't grab that instead.
    speed=$(echo "$output" | grep -oE '[0-9.]+c/s' | tail -1 | grep -oE '^[0-9.]+')
    if [ -z "$speed" ]; then
        echo "  WARNING: could not parse a speed value for $label"
    fi

    echo "\"$label\",\"$format\",\"${FILES[$i]}\",$speed" >> "$OUT"
done

echo ""
echo "Saved $N results to $OUT"
