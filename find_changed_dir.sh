find . \( -name ".git" -o -name "node_modules" \) -prune -o -type d -mmin -360 -print

