import random
import re

def roll(dice_str):
    match = re.fullmatch(r"(\d*)d(\d+)", dice_str)
    if not match:
        raise ValueError("Invalid dice format. Use XdY like 1d20.")

    num_dice = int(match.group(1)) if match.group(1) else 1
    dice_size = int(match.group(2))
    rolls = [random.randint(1, dice_size) for _ in range(num_dice)]
    return rolls, sum(rolls)
