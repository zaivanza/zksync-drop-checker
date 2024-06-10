from termcolor import cprint
import json
from pathlib import Path
import csv
import aiohttp
import asyncio
from loguru import logger

def load_json(filepath: Path | str):
    with open(filepath, "r") as file:
        return json.load(file)
    
def read_txt(filepath: Path | str):
    with open(filepath, "r") as file:
        return [row.strip() for row in file]
    
def call_json(result: list | dict, filepath: Path | str):
    with open(f"{filepath}.json", "w") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

async def fetch_wallet_data(session, wallet: str):
    while True:
        try:
            async with session.get(f"https://api.staging.zknation.io/allocation/{wallet}") as response:
                if response.status == 200:
                    data = await response.json()
                    return wallet, 0
                    return wallet, data
                else:
                    logger.error(f"{wallet} | response.status: {response.status} | try again...")
                    await asyncio.sleep(1)
        except Exception as error:
            logger.error(f"{wallet} | error: {error} | try again...")
            await asyncio.sleep(1)

async def check_wallets_chunk(session, wallets_chunk: list):
    tasks = [fetch_wallet_data(session, wallet) for wallet in wallets_chunk]
    results = await asyncio.gather(*tasks)
    return {wallet: data for wallet, data in results}

async def check_wallets(wallets: list):
    chunk_size = 10
    results = {}
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(wallets), chunk_size):
            wallets_chunk = wallets[i:i+chunk_size]
            chunk_results = await check_wallets_chunk(session, wallets_chunk)
            results.update(chunk_results)
            await asyncio.sleep(1)

    return results

class DropChecker:
    def __init__(self) -> None:
        self.wallets: list = [wallet.lower() for wallet in read_txt("wallets.txt")]

    def get_checked_wallets_old(self):
        eligible_wallets = []
        ineligible_wallets = []
        results = {}
        for wallet in self.wallets:
            if wallet in self.zksync_wallets:
                results[wallet] = float(self.zksync_wallets[wallet])
                eligible_wallets.append(wallet)
            else:
                results[wallet] = 0
                ineligible_wallets.append(wallet)
        return results, eligible_wallets, ineligible_wallets
    
    def main(self):
        results = asyncio.run(check_wallets(self.wallets))
        eligible_wallets = [wallet for wallet, reward in results.items() if reward]
        ineligible_wallets = [wallet for wallet, reward in results.items() if reward == 0]

        with open("results/eligible_wallets.txt", 'w') as file:
            for wallet in eligible_wallets:
                file.write(wallet + '\n')

        with open("results/ineligible_wallets.txt", 'w') as file:
            for wallet in ineligible_wallets:
                file.write(wallet + '\n')

        total_rewards = 0
        with open("results/results.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            
            writer.writerow(['ADDRESS', 'REWARD'])
            for address, reward in results.items():
                writer.writerow([address, reward])
                total_rewards += reward

                cprint(f"{address} | {reward}", "white")

        cprint("\n\nResults are recorded in results", "white")
        cprint(f"Eligible wallets: {len(eligible_wallets)} / {len(self.wallets)}\n", "green")
        cprint(f"Total rewards: {total_rewards} ZK\n", "blue")


