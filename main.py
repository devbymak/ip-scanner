#!/usr/bin/env python3
import ipaddress
import random
import sys
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import csv
import json

import requests
from tqdm import tqdm

FASTLY_CIDRS = [
    "103.244.50.0/24", "103.245.222.0/23", "103.245.224.0/24",
    "104.156.80.0/20", "146.75.0.0/16",   "151.101.0.0/16",
    "157.52.64.0/18","167.82.0.0/17",    "167.82.128.0/20",
    "167.82.160.0/20","167.82.224.0/20","172.111.64.0/18",
    "185.31.16.0/22","199.232.0.0/16",   "199.27.72.0/21",
    "23.235.32.0/20","43.249.72.0/22"
]

CLOUDFLARE_CIDRS = [
    "103.21.244.0/22",  "103.22.200.0/22", "103.31.4.0/22",
    "104.16.0.0/13",    "104.24.0.0/14",   "108.162.192.0/18",
    "131.0.72.0/22",    "141.101.64.0/18", "162.158.0.0/15",
    "172.64.0.0/13",    "173.245.48.0/20", "188.114.96.0/20",
    "190.93.240.0/20",  "197.234.240.0/22","198.41.128.0/17"
]

def fetch_bunny_ips():
    """
    Fetch Bunny CDN IP addresses from their API.
    Returns a list of IP addresses as strings.
    """
    try:
        response = requests.get("https://bunnycdn.com/api/system/edgeserverlist", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Bunny CDN IPs: {e}")
        return []

def generate_random_ips(networks, count):
    weights = [net.num_addresses for net in networks]
    chosen_nets = random.choices(networks, weights=weights, k=count)
    ips = []
    for net in chosen_nets:
        if net.num_addresses > 2:
            offset = random.randint(1, net.num_addresses - 2)
        else:
            offset = 0
        ips.append(net.network_address + offset)
    return ips

def generate_random_ips_from_list(ip_list, count):
    """
    Generate random IPs from a list of individual IP addresses.
    """
    if len(ip_list) == 0:
        return []
    
    # If count is greater than available IPs, return all IPs
    if count >= len(ip_list):
        return [ipaddress.IPv4Address(ip) for ip in ip_list]
    
    # Otherwise, randomly sample from the list
    chosen_ips = random.sample(ip_list, count)
    return [ipaddress.IPv4Address(ip) for ip in chosen_ips]

def test_ip(ip, timeout):
    """
    Returns (ip, elapsed_seconds) if the request finishes within `timeout` sec,
    regardless of HTTP status or other errors. Returns None on timeout.
    """
    start = time.monotonic()
    try:
        requests.get(f"http://{ip}", timeout=timeout)
    except requests.exceptions.Timeout:
        return None
    except Exception:
        elapsed = time.monotonic() - start
        return str(ip), elapsed
    else:
        elapsed = time.monotonic() - start
        return str(ip), elapsed

def check_ips(ips, workers, timeout):
    responsive = []
    futures_map = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for ip in ips:
            futures_map[executor.submit(test_ip, ip, timeout)] = ip

        with tqdm(total=len(futures_map), desc="Testing IPs") as pbar:
            for future in as_completed(futures_map):
                ip = futures_map[future]
                result = future.result()
                if result:
                    ip_str, elapsed = result
                    responsive.append((ip_str, elapsed))
                    pbar.set_postfix(ip=ip_str, time=f"{elapsed:.2f}s")
                else:
                    pbar.set_postfix(ip=ip, time="timeout")
                pbar.update()
    return responsive

def main():
    choice = input("Which network to test? [fastly/cloudflare/bunny]: ").strip().lower()
    if choice not in {"fastly", "cloudflare", "bunny"}:
        print("Please enter 'fastly', 'cloudflare', or 'bunny'.")
        sys.exit(1)

    if choice == "bunny":
        print("Fetching Bunny CDN IP addresses...")
        bunny_ips = fetch_bunny_ips()
        if not bunny_ips:
            print("Failed to fetch Bunny CDN IPs. Exiting.")
            sys.exit(1)
        print(f"Fetched {len(bunny_ips)} Bunny CDN IP addresses.")
        networks = None
        ip_list = bunny_ips
    else:
        cidr_list = FASTLY_CIDRS if choice == "fastly" else CLOUDFLARE_CIDRS
        networks = [ipaddress.IPv4Network(c) for c in cidr_list]
        ip_list = None

    try:
        count = int(input("Enter number of IPs to check: "))
        if count <= 0:
            raise ValueError
    except ValueError:
        print("Please enter a positive integer for count.")
        sys.exit(1)

    cpu_cores = multiprocessing.cpu_count()
    recommended = cpu_cores
    worker_input = input(f"Enter number of worker threads [recommended {recommended}]: ").strip()
    if worker_input == "":
        workers = recommended
    else:
        try:
            workers = int(worker_input)
            if workers <= 0:
                raise ValueError
        except ValueError:
            print("Invalid worker count; using recommended value.")
            workers = recommended

    timeout_input = input("Enter timeout in seconds [default 1]: ").strip()
    if timeout_input == "":
        timeout = 1.0
    else:
        try:
            timeout = float(timeout_input)
            if timeout <= 0:
                raise ValueError
        except ValueError:
            print("Invalid timeout; using default of 1 second.")
            timeout = 1.0

    if choice == "bunny":
        ips_to_test = generate_random_ips_from_list(ip_list, count)
    else:
        ips_to_test = generate_random_ips(networks, count)
    
    responsive = check_ips(ips_to_test, workers, timeout)

    # Prepare filename with timestamp
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"responsive_ips_{choice}_{now_str}.csv"

    if responsive:
        print("\nResponsive IPs and timings:")
        for ip, elapsed in responsive:
            print(f"{ip}, {elapsed:.2f}s")
        # Write CSV
        with open(filename, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ip", "response_time_s"])
            for ip, elapsed in responsive:
                writer.writerow([ip, f"{elapsed:.2f}"])
        print(f"\nSaved responsive IPs to {filename}")
    else:
        print(f"\nNo IPs responded within {timeout} second(s).")

if __name__ == "__main__":
    main()

