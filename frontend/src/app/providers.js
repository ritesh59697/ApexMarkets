"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { ethers } from "ethers";
import { ACTIVE_NETWORK } from "../utils/config";
import { defineChain } from "viem";
import { getDefaultConfig, RainbowKitProvider, darkTheme, lightTheme, useConnectModal } from "@rainbow-me/rainbowkit";
import { WagmiProvider, useAccount, useDisconnect, useSwitchChain, useConnectorClient } from "wagmi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export const WalletContext = createContext(null);

export function useWalletContext() {
  return useContext(WalletContext);
}

const arcMainnet = {
  ...defineChain({
    id: 5042,
    name: "Arc",
    nativeCurrency: { name: "USD Coin", symbol: "USDC", decimals: 6 },
    rpcUrls: {
      default: { http: ["https://rpc.mainnet.arc.io"] },
      public: { http: ["https://rpc.mainnet.arc.io"] },
    },
    blockExplorers: {
      default: { name: "Arc Explorer", url: "https://explorer.arc.io" },
    },
    testnet: false,
  }),
  iconUrl: "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
  iconBackground: "#004fd2",
};

const arcTestnet = {
  ...defineChain({
    id: 5042002,
    name: "Arc Testnet",
    nativeCurrency: { name: "USD Coin", symbol: "USDC", decimals: 6 },
    rpcUrls: {
      default: { http: ["https://rpc.testnet.arc.network"] },
      public: { http: ["https://rpc.testnet.arc.network"] },
    },
    blockExplorers: {
      default: { name: "Arcscan", url: "https://testnet.arcscan.app" },
    },
    testnet: true,
  }),
  iconUrl: "https://assets.coingecko.com/coins/images/6319/small/usdc.png",
  iconBackground: "#4f46e5",
};

const config = getDefaultConfig({
  appName: "ApexMarkets",
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "3a8170812b534d0ff9ec4b11c0ac5ba5",
  chains: [arcMainnet, arcTestnet],
  ssr: true,
});

const queryClient = new QueryClient();

function WalletBridge({ children }) {
  const { address, isConnected, isConnecting, chainId } = useAccount();
  const { disconnect } = useDisconnect();
  const { switchChain } = useSwitchChain();
  const { data: client } = useConnectorClient();
  const { openConnectModal } = useConnectModal();

  const [walletState, setWalletState] = useState({
    address: null,
    provider: null,
    signer: null,
    chainId: null,
    isConnected: false,
    isCorrectNetwork: false,
    isConnecting: false,
    error: null,
  });

  useEffect(() => {
    if (!isConnected) {
      setWalletState({
        address: null,
        provider: null,
        signer: null,
        chainId: null,
        isConnected: false,
        isCorrectNetwork: false,
        isConnecting: isConnecting,
        error: null,
      });
      return;
    }

    if (client) {
      const provider = new ethers.BrowserProvider(client.transport);
      provider.getSigner().then((signer) => {
        setWalletState({
          address: address || null,
          provider,
          signer,
          chainId: chainId || null,
          isConnected: true,
          isCorrectNetwork: chainId === ACTIVE_NETWORK.chainId,
          isConnecting: false,
          error: null,
        });
      }).catch((err) => {
        console.error("Failed to get ethers signer:", err);
      });
    } else {
      setWalletState((s) => ({
        ...s,
        address: address || null,
        chainId: chainId || null,
        isConnected: true,
        isCorrectNetwork: chainId === ACTIVE_NETWORK.chainId,
        isConnecting: isConnecting,
      }));
    }
  }, [client, address, isConnected, isConnecting, chainId]);

  const switchToArc = useCallback(async () => {
    try {
      await switchChain({ chainId: ACTIVE_NETWORK.chainId });
      return true;
    } catch (err) {
      console.error("Failed to switch network:", err);
      return false;
    }
  }, [switchChain]);

  const contextValue = {
    ...walletState,
    connect: openConnectModal || (() => {}),
    disconnect,
    switchToArc,
  };

  return (
    <WalletContext.Provider value={contextValue}>
      {children}
    </WalletContext.Provider>
  );
}

export function Providers({ children }) {
  const [currentTheme, setCurrentTheme] = useState("light");

  useEffect(() => {
    const checkTheme = () => {
      const stored = localStorage.getItem("arcmarkets-theme") || "light";
      setCurrentTheme(stored);
    };
    checkTheme();

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === "data-theme") {
          const t = document.documentElement.getAttribute("data-theme") || "light";
          setCurrentTheme(t);
        }
      });
    });

    observer.observe(document.documentElement, { attributes: true });
    return () => observer.disconnect();
  }, []);

  const customLightTheme = lightTheme({
    accentColor: "#004fd2",
    accentColorForeground: "#ffffff",
    borderRadius: "large",
    fontStack: "system",
    overlayBlur: "small",
  });

  const customDarkTheme = darkTheme({
    accentColor: "#2979ff",
    accentColorForeground: "#ffffff",
    borderRadius: "large",
    fontStack: "system",
    overlayBlur: "small",
  });

  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider
          theme={currentTheme === "dark" ? customDarkTheme : customLightTheme}
          modalSize="compact"
        >
          <WalletBridge>
            {children}
          </WalletBridge>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
