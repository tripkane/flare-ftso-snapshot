# Quick provider address to name mapping based on RPC + scraped data comparison
PROVIDER_ADDRESS_TO_NAME = {
    "0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c": "Bifrost Wallet",
    "0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22": "Flare.Space", 
    "0xbce1972de5d1598a948a36186ecebfd4690f3a5c": "AlphaOracle",
    "0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0": "Flare Oracle",
    "0x89e50dc0380e597ece79c8494baafd84537ad0d4": "Atlas TSO",
    "0xdbf71d7840934eb82fa10173103d4e9fd4054dd1": "NORTSO",
}

# Save this mapping
import json
with open('provider_address_mapping.json', 'w') as f:
    json.dump(PROVIDER_ADDRESS_TO_NAME, f, indent=2)

print("Created provider address mapping!")
print("Addresses mapped:")
for addr, name in PROVIDER_ADDRESS_TO_NAME.items():
    print(f"  {addr} -> {name}")
