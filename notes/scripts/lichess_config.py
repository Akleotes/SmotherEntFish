#!/usr/bin/env python3
"""Write lichess-bot's config.yml for Smotherfish from lichess-bot's own
config.yml.default (so every other setting keeps lichess-bot's default).

usage: lichess_config.py config.yml.default config.yml [THREADS] [HASH_MB]

The token is not written: lichess-bot reads it from the LICHESS_BOT_TOKEN
environment variable (a repository secret).
"""
import sys
import yaml

src, dst = sys.argv[1], sys.argv[2]
threads = int(sys.argv[3]) if len(sys.argv) > 3 else 3
hash_mb = int(sys.argv[4]) if len(sys.argv) > 4 else 2048
c = yaml.safe_load(open(src))

e = c["engine"]
e["dir"] = "./engines/"
e["name"] = "smotherfish"
e["protocol"] = "uci"
e["ponder"] = True
# Threads: one core is left for the smother prover's own thread.
e["uci_options"] = {"Threads": threads, "Hash": hash_mb, "Move Overhead": 150}
e["polyglot"]["enabled"] = False

ch = c["challenge"]
ch["concurrency"] = 1
ch["accept_bot"] = True
ch["only_bot"] = False
ch["time_controls"] = ["bullet", "blitz", "rapid"]
ch["modes"] = ["casual", "rated"]
ch["variants"] = ["standard"]

mm = c["matchmaking"]
mm["allow_matchmaking"] = True
mm["challenge_variant"] = "standard"
mm["challenge_timeout"] = 1          # challenge a bot after 1 idle minute
mm["challenge_initial_time"] = [180, 300]
mm["challenge_increment"] = [2, 3]
mm["challenge_mode"] = "rated"
mm["opponent_rating_difference"] = 400

c["pgn_directory"] = "game_records"
c["pgn_file_grouping"] = "game"
c["quit_after_all_games_finish"] = True  # Ctrl-C (SIGINT) lets games finish

yaml.safe_dump(c, open(dst, "w"), sort_keys=False)
print(f"wrote {dst}: Threads {threads}, Hash {hash_mb}, matchmaking "
      f"{mm['challenge_initial_time']}+{mm['challenge_increment']} {mm['challenge_mode']}")
