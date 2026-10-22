const hre = require("hardhat");
const { ethers } = hre;
const fs = require("fs");

/**
 * Executes a live USDC prediction transaction on Arc Mainnet
 * to satisfy the Arc Microgrants requirement.
 * Run: npx hardhat run scripts/execute-mainnet-tx.js --network arcMainnet
 */
async function main() {
  const [signer] = await ethers.getSigners();
  console.log("=========================================");
  console.log("EXECUTING ARC MAINNET USDC TRANSACTION");
  console.log("=========================================");
  console.log("Account:  ", signer.address);

  const balance = await ethers.provider.getBalance(signer.address);
  console.log("Balance:  ", ethers.formatEther(balance), "USDC");

  if (balance === 0n) {
    throw new Error("Account has 0 USDC balance on Arc Mainnet. Please fund with a small amount of USDC for gas and wager.");
  }

  // Load deployment addresses
  let deployment;
  try {
    deployment = JSON.parse(fs.readFileSync("deployment.json", "utf8"));
  } catch (err) {
    throw new Error("deployment.json not found. Run deployment first!");
  }

  const marketAddress = deployment.marketAddress;
  const usdcAddress = deployment.usdcAddress || "0x3600000000000000000000000000000000000000";

  console.log("Market:   ", marketAddress);
  console.log("USDC:     ", usdcAddress);

  const market = await ethers.getContractAt("PredictionMarket", marketAddress);
  const matchCount = await market.getMatchCount();
  console.log("Matches available:", matchCount.toString());

  if (matchCount === 0n) {
    console.log("Creating a match fixture...");
    const now = Math.floor(Date.now() / 1000);
    const tx = await market.createMatch("Brazil", "Argentina", "MAINNET_MATCH_001", now + 86400 * 3);
    await tx.wait();
    console.log("Match created!");
  }

  const matchIndex = 0;
  const betAmount = 10000n; // 0.01 USDC (minimum bet)

  console.log(`\n1. Approving ${ethers.formatUnits(betAmount, 6)} USDC for PredictionMarket...`);
  const usdc = await ethers.getContractAt("IERC20", usdcAddress);
  const approveTx = await usdc.approve(marketAddress, betAmount);
  console.log("   Approve tx submitted:", approveTx.hash);
  await approveTx.wait();
  console.log("   Approve confirmed ✓");

  console.log(`\n2. Placing wager on Match #${matchIndex} (Outcome: HOME_WIN, 0.01 USDC)...`);
  const betTx = await market.placeBet(matchIndex, 1, betAmount);
  console.log("   Bet tx submitted:", betTx.hash);
  const receipt = await betTx.wait();
  console.log("   Bet confirmed in block:", receipt.blockNumber, "✓");

  console.log("\n=========================================");
  console.log("🎉 SUCCESS! MAINNET TRANSACTION RECORDED");
  console.log("=========================================");
  console.log("Transaction Hash:");
  console.log(receipt.hash);
  console.log("\nExplorer Link for DoraHacks Submission:");
  console.log(`https://explorer.arc.io/tx/${receipt.hash}`);
  console.log("=========================================\n");
}

main().catch((err) => {
  console.error("Failed:", err.message);
  process.exit(1);
});
