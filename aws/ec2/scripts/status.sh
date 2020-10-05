find . -name "*.log" -exec ls -l {} \; | grep -v "Mar 18" | fgrep -v done | fgrep -v "$1"
