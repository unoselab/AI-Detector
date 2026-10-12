echo "===== OS ====="
lsb_release -a

echo "===== CPU ====="
lscpu

echo "===== RAM ====="
free -h

echo "===== GPU ====="
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi
else
    lspci | grep -iE 'vga|3d|display'
fi

echo "===== DISK ====="
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS
df -h

echo "===== KERNEL ====="
uname -a
