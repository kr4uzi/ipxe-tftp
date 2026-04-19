# Why?
iPXE's shim depends on its own filename - which mandy UEFI firmwares do not provide.
Therefore a platform specific (x86_64 / arm64) and binary specific (snponly.efi / ipxe.efi) loading will not work.

expected behaviour:
ipxeboot/x86_64-sb/snponly-shim.efi -> ipxeboot/x86_64-sb/snponly.efi

actual behaviour on MacOS Parallels, Asus H87M-Pro, Igel M340, exone Notebook, Surface Laptop 3:
ipxeboot/x86_64-sb/snponly-shim.efi -> ipxe.efi

To see if your hardware is affected by this, compile the pxeinfo:\
This folder contains a very basic verification EFI which prints out the loaded file path - which if empty means that the currentl running firmware doesn't support iPXE's automatic shim loading.

# Setup
Copy tftp.py and ipxe-tftp.service to /srv/ipxe-tftp, then install the dependency:
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fbtftp
chmod +x tftp.py
```

The script assumes that the pxe files are at /srv/pxe and the ipxe files are at /srv/pxe/ipxeboot (netboot binaries).

# Run
`.venv/bin/python tftp.py`

# Daemon (systemd)
```sh
cp -v ipxe-tftp.service /etc/systemd/system
systemctl enable ipxe-tftp          #enable service
systemctl start ipxe-tftp           #start service
systemctl status ipxe-tftp          #check if the service started
journalctl -u ipxe-tftp -f          #inspect the logs

#Remove
systemctl stop ipxe-tftp
systemctl disable ipxe-tftp
systemctl daemon-reload
```