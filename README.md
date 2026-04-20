# Overview
iPXE's shim depends on its own filename - which is many UEFI firmwares do not support.

expected:\
ipxeboot/x86_64-sb/snponly-shim.efi -> ipxeboot/x86_64-sb/snponly.efi

actual:\
ipxeboot/x86_64-sb/snponly-shim.efi -> ipxe.efi

=> the shim has a builtin fallback /ipxe.efi which means you won't be able to have a cross platform boot

# alternatives
This TFTP server is *only* usefull if you need to:
- load snponly.efi
- secureboot
- multiple architectures

Simply symlink the snonly.efi from the architecture you need to support to the tftp root as ipxe.efi

e.g. x86_64:
ln -s /srv/pxe/ipxeboot/x86_64-sb/snponly.efi /srv/pxe/ipxe.efi

If you need secureboot and ipxe.efi (not snponly.efi) for multiple architectures, do not use the netboot package, but the ISO instead, as there the BOOTX64.EFI and BOOTAA64.EFI are signed directly and *do not need the shim*.

# pxeinfo
To verify wether a machine is affected by this firmware bug, you can compile (and boot) the small EFI program in the pxeinfo folder in this repository.

If the output is empty, your firmware won't support iPXE's shim-based secureboot.

# Setup
Copy tftp.py and ipxe-tftp.service to /srv/ipxe-tftp, then install the dependency:
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fbtftp
chmod +x tftp.py
```

The script assumes that the TFTP root is /srv/pxe (adjust line 85 in tftp.py if that's not the case)

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