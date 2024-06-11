from termcolor import cprint
import json
from pathlib import Path
import csv
import aiohttp
import asyncio
from loguru import logger
import random

def decimalToInt(qty, decimal):
    return float(qty / 10**decimal)

def load_json(filepath: Path | str):
    with open(filepath, "r") as file:
        return json.load(file)
    
def read_txt(filepath: Path | str):
    with open(filepath, "r") as file:
        return [row.strip() for row in file]
    
def call_json(result: list | dict, filepath: Path | str):
    with open(f"{filepath}.json", "w") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

def get_headers():
    return {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        # 'if-none-match': 'W/"25d-9gfVZf/yh9tyCXyEiIgyQM2Dh/4"',
        'origin': 'https://claim.zknation.io',
        'priority': 'u=1, i',
        'referer': 'https://claim.zknation.io/',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'x-api-key': '46001d8f026d4a5bb85b33530120cd38',
    }

async def fetch_wallet_data(session, wallet: str, proxies: list):
    while True:
        try:
            async with session.get(
                url=f"https://api.zknation.io/eligibility", 
                params={'id': wallet},
                headers=get_headers(),
                proxy=random.choice(proxies)
                ) as response:
                if response.status == 200:
                    data = await response.json()
                    reward = decimalToInt(int(data["allocations"][0]["tokenAmount"]), 18) if data["allocations"] else 0
                    cprint(f"{wallet} | {reward}", "white")
                    return wallet, reward
                else:
                    logger.error(f"{wallet} | response.status: {response.status} | try again...")
                    await asyncio.sleep(1)
        except Exception as error:
            logger.error(f"{wallet} | error: {error} | try again...")
            await asyncio.sleep(3)

async def check_wallets_chunk(session, wallets_chunk: list, proxies: list):
    tasks = [fetch_wallet_data(session, wallet, proxies) for wallet in wallets_chunk]
    results = await asyncio.gather(*tasks)
    return {wallet: data for wallet, data in results}

async def check_wallets(wallets: list, proxies: list):
    chunk_size = 10
    results = {}
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(wallets), chunk_size):
            wallets_chunk = wallets[i:i+chunk_size]
            chunk_results = await check_wallets_chunk(session, wallets_chunk, proxies)
            results.update(chunk_results)
            await asyncio.sleep(1)

    return results

class DropChecker:
    def __init__(self) -> None:
        self.wallets: list = [wallet.lower() for wallet in read_txt("wallets.txt")]
        self.proxies = read_txt("proxies.txt")

    def main(self):
        results = asyncio.run(check_wallets(self.wallets, self.proxies))
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
                # cprint(f"{address} | {reward}", "white")

        cprint("\n\nResults are recorded in results", "white")
        cprint(f"Eligible wallets: {len(eligible_wallets)} / {len(self.wallets)}\n", "green")
        cprint(f"Total rewards: {total_rewards} ZK\n", "blue")


