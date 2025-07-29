# Blockchain Method Research

This folder contains experimental scripts and research for extracting FTSO vote power data directly from the Flare blockchain using RPC calls.

## Status: Experimental / On Hold

The blockchain direct approach was put on hold to focus on improving the site interface and user experience. While we made progress understanding the blockchain structure, we didn't achieve the exact vote power values shown in the Flare FTSO Statistics dashboard.

## Files Overview

### Core RPC Infrastructure
- `flare_rpc_new.py` - Updated RPC calling functions using Ankr API
- `current_vote_power_rpc.py` - Main script for fetching vote power via RPC

### Contract Discovery & Analysis
- `blockchain_exploration.py` - Systematic exploration of Flare contracts
- `find_contracts.py` - Dynamic contract address discovery via FlareContractRegistry
- `debug_registry.py` - Debug FlareContractRegistry interface

### Vote Power Investigation
- `get_bifrost_vote_power.py` - Focused script to get Bifrost Wallet's exact vote power
- `debug_vote_power_events.py` - Debug vote power event extraction and scaling
- `find_wnat_balances.py` - Search for WNat balances and delegation data

## Key Findings

### Contracts Identified
- VotePowerContract: `0x1000000000000000000000000000000000000002`
- FlareContractRegistry: `0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019`
- WNat Contract: `0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d`

### Provider Addresses Discovered
- Bifrost Wallet: `0x4d92ba6d90df99f7f25dc5b53b1697957e02a02c`
- Flare.Space: `0x7b61f9f27153a4f2f57dc30bf08a8eb0ccb96c22`
- AlphaOracle: `0xbce1972de5d1598a948a36186ecebfd4690f3a5c`
- Flare Oracle: `0x9c7a4c83842b29bb4a082b0e689cb9474bd938d0`
- Atlas TSO: `0x89e50dc0380e597ece79c8494baafd84537ad0d4`
- NORTSO: `0xdbf71d7840934eb82fa10173103d4e9fd4054dd1`

### Event Analysis
- Vote power events signature: `0xe7aa66356adbd5e839ef210626f6d8f6f72109c17fadf4c4f9ca82b315ae79b4`
- Events show small incremental values, not total vote power
- Need ~99,461x multiplier to match dashboard values
- Target for Bifrost: 1,683,080,166 (from Flare FTSO Statistics)
- Actual from events: 16,922

## Challenges Encountered

1. **Scale Mismatch**: Event data shows much smaller values than expected
2. **Contract Interface**: Many contract calls revert, suggesting wrong function signatures
3. **Data Source**: Vote power events may show incremental changes, not totals
4. **Documentation Gap**: Limited documentation on exact contract interfaces for vote power queries

## Next Steps (When Resumed)

1. Investigate FSP (Flare Systems Protocol) VoterRegistry contract
2. Look for aggregated vote power functions rather than individual events
3. Research WNat delegation patterns and delegation weight calculations
4. Consider using Flare Transaction SDK for proper contract interaction

## Test Data Separation

The RPC data files generated during testing are kept separate from production scraped data. They can be identified by:
- Human-readable provider names (NORTSO, Bifrost Wallet, etc.)
- Often showing 0% vote power values
- Located in `current_vote_power/` with RPC-style naming

Production scraped data shows:
- Generic provider names like "Provider_0x7d9f...d06b"
- Actual vote power percentages
- Proper vote power distribution
