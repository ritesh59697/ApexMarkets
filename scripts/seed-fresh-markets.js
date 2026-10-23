const { ethers } = require("ethers");
require("dotenv").config();

async function main() {
  const rpcUrl = "https://arc-testnet.g.alchemy.com/v2/dsKUaW_GE724U3laOjGG2";
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const privateKey = process.env.PRIVATE_KEY;
  const wallet = new ethers.Wallet(privateKey, provider);
  
  console.log("Seeding fresh markets on Arc Testnet...");
  console.log("Account:", wallet.address);
  
  const marketAddress = "0xbE2bf8f1c34a0517Dfd8732d4b8A82056DB539B4";
  const abi = [
    "function createMatch(string,string,string,uint256) returns (uint256)",
    "function getMatchCount() view returns (uint256)"
  ];
  
  const market = new ethers.Contract(marketAddress, abi, wallet);
  const currentCount = await market.getMatchCount();
  console.log("Current match count:", currentCount.toString());

  const now = Math.floor(Date.now() / 1000);
  
  const freshMarkets = [
    {
      home: "Brazil",
      away: "Argentina",
      id: "FB_BRA_ARG_2026_Q4",
      kickoff: now + 86400 * 7 // in 7 days
    },
    {
      home: "BTC Above $105K",
      away: "BTC Below $102K",
      id: "CR_BTC_105K_Q4",
      kickoff: now + 86400 * 5 // in 5 days
    },
    {
      home: "France",
      away: "Germany",
      id: "FB_FRA_GER_2026_Q4",
      kickoff: now + 86400 * 10 // in 10 days
    },
    {
      home: "ETH Outperforms SOL",
      away: "SOL Outperforms ETH",
      id: "CR_ETH_SOL_2026_Q4",
      kickoff: now + 86400 * 8 // in 8 days
    },
    {
      home: "Solana",
      away: "BNB",
      id: "CR_SOL_BNB_2026_Q4",
      kickoff: now + 86400 * 12 // in 12 days
    },
    {
      home: "AI Tokens",
      away: "Meme Tokens",
      id: "CR_AI_MEME_2026_Q4",
      kickoff: now + 86400 * 14 // in 14 days
    },
    {
      home: "Spain",
      away: "England",
      id: "FB_ESP_ENG_2026_Q4",
      kickoff: now + 86400 * 16 // in 16 days
    }
  ];

  for (const m of freshMarkets) {
    console.log(`Creating: ${m.home} vs ${m.away} (kickoff in ${Math.round((m.kickoff - now)/86400)} days)...`);
    try {
      const tx = await market.createMatch(m.home, m.away, m.id, m.kickoff);
      console.log(`  Tx sent: ${tx.hash}`);
      const receipt = await tx.wait();
      console.log(`  Confirmed in block ${receipt.blockNumber} ✓`);
    } catch (e) {
      console.error(`  Failed:`, e.message);
    }
  }

  const newCount = await market.getMatchCount();
  console.log("\nDone! New match count:", newCount.toString());
}

main().catch(console.error);
