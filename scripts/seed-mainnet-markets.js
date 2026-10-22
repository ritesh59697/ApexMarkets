const hre = require("hardhat");
const { ethers } = hre;
const fs = require("fs");

/**
 * Seeds additional live markets on Arc Mainnet for a rich UI display.
 * Run: npx hardhat run scripts/seed-mainnet-markets.js --network arcMainnet
 */
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Seeding markets with:", deployer.address);
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Current Balance:", ethers.formatEther(balance), "USDC");

  const deployment = JSON.parse(fs.readFileSync("deployment.json", "utf8"));
  const market = await ethers.getContractAt("PredictionMarket", deployment.marketAddress);

  const currentCount = await market.getMatchCount();
  console.log(`Current match count: ${currentCount}`);

  const now = Math.floor(Date.now() / 1000);
  const day = 86400;

  const newMatches = [
    { home: "France", away: "Germany", id: "SPORT_WC26_002", kickoff: now + day * 4 },
    { home: "ETH Outperforms SOL", away: "SOL Outperforms ETH", id: "CRYPTO_ETH_SOL_001", kickoff: now + day * 2 },
    { home: "AI Tokens", away: "Meme Tokens", id: "CRYPTO_SECTOR_001", kickoff: now + day * 3 },
  ];

  for (const m of newMatches) {
    console.log(`Creating: ${m.home} vs ${m.away} (${m.id})...`);
    const tx = await market.createMatch(m.home, m.away, m.id, m.kickoff);
    await tx.wait();
    console.log(`   Confirmed ✓`);
  }

  const updatedCount = await market.getMatchCount();
  console.log(`\nAll ${updatedCount} Markets Live on Arc Mainnet:`);
  for (let i = 0; i < updatedCount; i++) {
    const m = await market.matches(i);
    console.log(` - #${i}: ${m.homeTeam} vs ${m.awayTeam} (Pool: ${ethers.formatUnits(m.totalPool, 6)} USDC)`);
  }

  const finalBalance = await ethers.provider.getBalance(deployer.address);
  console.log("\nFinal Balance:", ethers.formatEther(finalBalance), "USDC");
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
