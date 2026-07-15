echo
echo "============== [ Current working directory ] =============="
pwd

echo
echo "============== [ Files in current directory ] =============="
ls -1 .

echo
echo "============== [ src directory structure ] =============="

find src \
  \( -type d -name logs -o -path 'src/app/bak' \) -prune -o \
  \( -type f -name '*.csv' \) -prune -o \
  \( -type f -name '*.tsv' \) -prune -o \
  \( -type f -name '*.pkl' \) -prune -o \
  \( -type f -name 'mixed_sample_*.py' \) -prune -o \
  -print \
  | tree --fromfile --noreport