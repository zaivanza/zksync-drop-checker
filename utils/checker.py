from termcolor import cprint
import json
from pathlib import Path
import csv

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

def get_zksync_eligible_wallets():
    wallets = {}
    cprint(f"Start checking eligible wallets...", "white")
    with open("eligibility_list.csv", newline='') as csvfile:
        data = csv.DictReader(csvfile)
        for i, row in enumerate(data):
            if "userId" in row:
                address = row["userId"].lower()
                reward = int(row["tokenAmount"])
                wallets[address] = reward
    cprint(f"Found {len(wallets)} eligible wallets", "white")
    return wallets


def check_wallets(wallets: list):
    zksync_eligible_wallets = get_zksync_eligible_wallets()
    results = {}
    for wallet in wallets:
        if wallet in zksync_eligible_wallets:
            results[wallet] = zksync_eligible_wallets[wallet]
        else:
            results[wallet] = 0

    return results

class DropChecker:
    def __init__(self) -> None:
        self.wallets: list = [wallet.lower() for wallet in read_txt("wallets.txt")]

    def main(self):
        results = check_wallets(self.wallets)
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


