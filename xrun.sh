echo
echo "============== [ Current working directory ] =============="
pwd

echo
echo "============== [ Files in current directory ] =============="
ls -1 .

echo
echo "============== [ src directory structure, excluding logs ] =============="
tree --noreport -I 'logs' src