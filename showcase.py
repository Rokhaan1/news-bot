"""
One-time showcase: post ONE example from each news pillar so you can judge
quality (AI voice + branded graphic). Spaced out to avoid throttling.
Run manually from the Actions tab ("Showcase") — not on a schedule.
"""
import time

import config
import writer
from verify import is_corroborated
from main import (collect_entries, is_negative_afghan, post_news, make_client)


def post_with_retry(client, api_v1, entry, pillar, text, tries=3):
    for i in range(tries):
        try:
            post_news(client, api_v1, entry, pillar, text)
            return True
        except Exception as e:
            print(f"  retry {i+1}/{tries} [{pillar}]: {e}")
            time.sleep(8)
    return False


def main():
    client, api_v1 = make_client()
    for pillar, spec in config.PILLARS.items():
        entries = collect_entries(pillar, spec)
        done = False
        for entry in entries:
            if spec["hard_news"] and not is_corroborated(entry, entries):
                continue
            if pillar == "afghan_cricket" and is_negative_afghan(entry["title"]):
                continue
            result = writer.write_news(pillar, entry["title"], entry["source"])
            if result["skip"]:
                continue
            if post_with_retry(client, api_v1, entry, pillar, result["text"]):
                print(f"POSTED [{pillar}] {entry['title'][:60]}")
                done = True
                break
        if not done:
            print(f"NO EXAMPLE found for [{pillar}] this run")
        time.sleep(25)  # space posts out so X doesn't throttle
    print("Showcase complete.")


if __name__ == "__main__":
    main()
