def calculate_fiberhome_password(ssid):

    if not ssid.startswith("fh_") or len(ssid) != 9:
        return None
    try:
        hex_a = ssid[3:]
        hex_a_val = int(hex_a, 16)
        hex_b_val = 0xFFFFFF - hex_a_val
        return f"wlan{hex_b_val:06x}"
    except ValueError:
        return None

def main():
    print("🔍 FiberHome Password Calculator")
    print("=" * 35)
    ssid = input("📡 Entrez le SSID (ex: fh_654638): ").strip()
    
    if not ssid:
        print("❌ SSID vide.")
        return
    
    password = calculate_fiberhome_password(ssid)
    
    if password:
        print(f"\n✅ SSID     : {ssid}")
        print(f"🔑 Password : {password}")
    else:
        print(f"\n❌ '{ssid}' n'est pas un SSID FiberHome valide.")
        print("   (doit commencer par 'fh_' et faire 9 caractères)")

if __name__ == "__main__":
    main()