# Linux drills — shell one-liners and system questions (★ both reported for this role)

Type each one on your own machine (macOS has most; use a Linux VM/container for `ss`, `ip`,
`journalctl`). Say what each pipe stage does. Interviewers accept any correct approach; they
probe whether you know *why* it works and where it breaks (spaces in filenames, huge inputs).

## A. Filesystem traversal (Linux Engineer intern round: "shell one-liner about traversing the filesystem")

1. Largest 10 files under /var, human sizes:
   `find /var -xdev -type f -printf '%s %p\n' 2>/dev/null | sort -nr | head | numfmt --field=1 --to=iec`
   (macOS/BSD find lacks -printf: `find /var -type f -exec stat -f '%z %N' {} + | sort -nr | head`)
2. Which directory is eating the disk: `du -xh --max-depth=1 / 2>/dev/null | sort -h | tail`
3. Files modified in the last 2 days under /etc: `find /etc -type f -mtime -2 -ls`; since a timestamp: `-newermt '2026-09-13 09:00'`
4. Files owned by nobody (deleted user): `find / -xdev -nouser -o -nogroup`
5. Count files per extension in a tree: `find . -type f | sed -n 's/.*\.//p' | sort | uniq -c | sort -rn | head`
6. Safe loop over filenames with spaces: `find . -name '*.log' -print0 | xargs -0 grep -l ERROR`
7. Delete logs older than 30 days: `find /var/log/app -name '*.log' -mtime +30 -delete` (dry-run first without `-delete`)
8. Deleted-but-open files still holding space: `lsof +L1` or `find /proc/*/fd -ls 2>/dev/null | grep '(deleted)'`
9. Inodes exhausted: `df -i`; who has the most files: `for d in /*; do echo "$(find "$d" -xdev 2>/dev/null | wc -l) $d"; done | sort -n | tail`
10. Follow symlinks to the real file: `readlink -f path`; find broken symlinks: `find . -xtype l`

## B. Text processing on logs

1. Top 10 IPs in an access log: `awk '{print $1}' access.log | sort | uniq -c | sort -rn | head`
2. Requests per minute: `awk '{print substr($4,2,17)}' access.log | uniq -c` (assumes sorted by time)
3. 5xx lines with 3 lines of context: `grep -n -B3 -A3 ' 50[0-9] ' access.log`
4. Lines between two timestamps: `awk '$0 >= "2026-09-15T09:00" && $0 <= "2026-09-15T09:30"' app.log` (works because ISO timestamps sort lexically)
5. Sum bytes column: `awk '{s+=$10} END {print s}'`
6. Unique error messages ignoring the timestamp and pid: `sed -E 's/^[^ ]+ [^ ]+ //; s/\[[0-9]+\]//' app.log | sort | uniq -c | sort -rn | head`
7. Follow a log and highlight errors: `tail -F app.log | grep --line-buffered -E 'ERROR|WARN'`
8. Join two files on a key: `join <(sort a.txt) <(sort b.txt)`; set difference: `comm -23 <(sort a) <(sort b)`
9. Convert epoch to human: `date -d @1757900000` (macOS: `date -r`); `journalctl -o short-iso`
10. Columns to a table: `column -t`; JSON: `jq '.items[] | select(.state=="down") | .name'`
11. Replace in place across files: `grep -rl OLD dir | xargs sed -i 's/OLD/NEW/g'` (macOS: `sed -i ''`)
12. Count per hour from syslog: `awk '{print $3}' syslog | cut -d: -f1 | sort | uniq -c`

## C. Networking one-liners

1. My addresses/routes/neighbours: `ip -br addr; ip route; ip neigh`
2. Which process listens on 8080: `ss -ltnp 'sport = :8080'` (or `lsof -iTCP:8080 -sTCP:LISTEN`)
3. Count TCP states: `ss -tan | awk 'NR>1{print $1}' | sort | uniq -c`
4. Established connections per remote IP: `ss -tn state established | awk 'NR>1{split($4,a,":"); print a[1]}' | sort | uniq -c | sort -rn | head`
5. Is port open: `nc -zv host 443`; `timeout 2 bash -c '</dev/tcp/host/443' && echo open`
6. Capture BGP to a file, 1000 packets: `tcpdump -ni eth0 -c 1000 -w bgp.pcap 'tcp port 179'`
7. Show SYNs only: `tcpdump -ni eth0 'tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) == 0'`
8. Multicast joins: `tcpdump -ni eth0 igmp`; group membership: `ip maddr show`; `cat /proc/net/igmp`
9. Interface errors: `ip -s link show eth0`; `ethtool -S eth0 | grep -Ei 'err|drop|miss'`
10. Path MTU: `ping -M do -s 1472 host`; `tracepath host`
11. DNS: `dig +short A host`, `dig +trace host`, `dig -x 10.0.0.5`, `resolvectl query host`
12. Bandwidth test: `iperf3 -s` / `iperf3 -c host -P 4 -t 10`; UDP: `-u -b 1G`
13. Which core handles the NIC IRQs: `grep eth0 /proc/interrupts`; softnet drops: `awk '{print $2}' /proc/net/softnet_stat` (2nd column, hex)
14. ARP for a MAC on the LAN without traffic: `arping -I eth0 10.0.0.1`
15. Watch a counter: `watch -d -n1 'ethtool -S eth0 | grep rx_missed'`
16. LLDP neighbour (which switch port am I on): `lldpcli show neighbors` / `tcpdump -ni eth0 -v ether proto 0x88cc -c1`

## D. Processes, memory, CPU, disk

1. Process using the most memory: `ps aux --sort=-rss | head -5`
2. What is a stuck process doing: `cat /proc/PID/status | grep State`; `cat /proc/PID/wchan`; `sudo cat /proc/PID/stack`; `strace -p PID -f -tt` (which syscall is it blocked in; `futex` = waiting on a lock, `read` on fd N → `ls -l /proc/PID/fd/N`)
3. Open files of a process: `ls -l /proc/PID/fd | wc -l`; limit: `cat /proc/PID/limits`
4. Who is writing to disk: `iotop -o`; `pidstat -d 1`
5. System-wide: `vmstat 1 5` (r = runnable, b = blocked, si/so = swap, wa = I/O wait), `mpstat -P ALL 1`, `iostat -x 1`
6. OOM history: `dmesg -T | grep -i -A5 'killed process'`; `journalctl -k | grep -i oom`
7. Memory breakdown: `free -m` (available, not free, is what matters), `cat /proc/meminfo | grep -E 'MemAvail|Dirty|Slab|HugePages'`
8. Kill a process tree: `pkill -TERM -P PID`; after grace: `-KILL`
9. Run in background surviving logout: `nohup cmd &` / `setsid` / `tmux`
10. Limits: `ulimit -n`; systemd unit `LimitNOFILE=`
11. Service logs since boot: `journalctl -b -u sshd`; follow: `-f`; errors only: `-p err`
12. Timers/cron: `systemctl list-timers --all`; `crontab -l`; `/etc/cron.d`
13. Time sync: `chronyc tracking`; `timedatectl`
14. Kernel params: `sysctl -a | grep tcp_rmem`; persistent in `/etc/sysctl.d/`

## E. Scripting questions they ask verbally

- **Difference between `$*` and `$@`?** `"$@"` preserves argument boundaries; `"$*"` joins with IFS.
- **Why `set -euo pipefail`?** Exit on error, on unset variable, and fail a pipeline if any stage fails.
- **`>` vs `>>` vs `2>&1` vs `&>`?** Truncate, append, redirect stderr into stdout (order matters), both.
- **Exit codes?** `$?`; 0 success; 1–125 app; 126 not executable; 127 not found; 128+N killed by signal N.
- **Why `xargs -0` / `-print0`?** Filenames may contain spaces/newlines.
- **`grep -F` vs `-E` vs `-P`?** Fixed strings, extended regex, PCRE.
- **Test a variable is empty?** `[ -z "$x" ]`; file exists `[ -f ]`, dir `[ -d ]`, readable `[ -r ]`.
- **Difference between hard and soft link?** Same inode vs a path pointer; hard links can't cross filesystems or point at directories.
- **Permissions 755 / 644 / setuid / sticky bit?** rwxr-xr-x, rw-r--r--, run as owner, only owner can delete in dir (/tmp).
- **How do you make a script idempotent?** Check state before changing it; use `mkdir -p`, `ln -sfn`, conditional edits; exit non-zero on failure.
- **Python vs bash for automation?** Bash for glue and one-offs; Python when there's parsing, error handling, structured data (JSON/YAML), APIs, or tests.

## F. Small scripting tasks to do on the spot (write them, run them)

1. Parse `ip -br addr` output into JSON `{iface: [ips]}`.
2. Given a file of `host,ip` lines, ping each in parallel (bounded to 20 at a time) and print the ones that fail. (`xargs -P 20` or Python `concurrent.futures`.)
3. Tail a log and alert when the same error appears more than 5 times in a minute.
4. Convert a list of CIDRs to the minimal set (see `ip-tools.py` Part 3) — in shell it's the argument for Python.
5. Diff two `show running-config` dumps ignoring timestamps and line order within sections (see `config-tree.py`).
6. Compute per-second rate from a counter file with lines `ts value` (handle resets).
7. Find hosts in an inventory whose sshd version is below X by running `ssh host 'sshd -V'` in parallel with a timeout, collecting failures separately.

## G. Sample verbal Linux questions with 2-line answers

- *Process in state D for minutes; what's happening?* Uninterruptible sleep, usually I/O (NFS hang, dying disk). `cat /proc/PID/stack`, `dmesg` for I/O errors; can't be killed until the I/O returns.
- *Load average 40 on an 8-core box but CPU idle?* Load counts D-state processes too → I/O or NFS stall, not CPU.
- *`free` shows 2 GB free of 64 GB, is that a problem?* No: buff/cache is reclaimable; look at "available" and swap activity.
- *Disk shows 100% used but `du` sums to 60%?* Deleted-but-open files (`lsof +L1`), reserved blocks (5% for root), or a mount hiding files underneath.
- *`Too many open files`?* Per-process fd limit (`ulimit -n`, `LimitNOFILE`) or system-wide `fs.file-max`; find leaks with `ls /proc/PID/fd | wc -l`.
- *Service starts by hand but not under systemd?* Environment/PATH, working directory, user, dependencies (`After=network-online.target`), `journalctl -xeu`.
- *How do you know a NIC is dropping?* `ethtool -S` rx_missed/rx_no_buffer, `ip -s link` RX dropped, `/proc/net/softnet_stat` 2nd column, `nstat` UdpRcvbufErrors.
- *Clock is off by 3 minutes, what breaks?* Kerberos/TLS, log correlation, distributed locks, regulatory timestamps; check `chronyc tracking`, NTP reachability (UDP 123 filtered?).
