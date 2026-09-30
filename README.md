# WELCOME TO ZEBRA FINANCE-THE GAME!

Explore your financial habits in a fun and interactive way!

A small zebra runner that shows what a bank balance is likely to do next.
Money in is a coin. Money out is a rock. The zebra runs the next few weeks of the account.

This is a forecast, not a promise and not financial advice. It can be wrong.

## Who it is for

Someone who wants a quick feel for upcoming debit orders and payday before the balance goes negative.
It was built for the Investec Programmable Banking Q3 2026 bounty.

## What Investec data it uses

Sandbox or live Programmable Banking, South Africa:

- `POST /identity/v2/oauth2/token` for a client-credentials token
- `GET /za/pb/v1/accounts` and the Private Bank Account
- `GET /za/pb/v1/accounts/{id}/balance` for the starting balance
- `GET /za/pb/v1/accounts/{id}/transactions` for history

Investec sends amounts as positive numbers. `type: DEBIT` is stored as negative. `type: CREDIT` stays positive.

If `INVESTEC_CLIENT_ID` is empty, or the call fails, the game uses a built-in sample (DSTV, gym, salary, starting R4500) so the window still opens.

## How the forecast works

- Outflows with the same description at least twice, or whose text contains `DEBIT ORDER`, `NAEDO`, or `MAGTAPE`, become a monthly rock.
- The amount is the median of that group. The day of the month is the median day, capped at 28.
- Large inflows become one payday coin on `PAYDAY_DAY` (default 25), using the median of the biggest credits.
- The balance is walked forward for `FORECAST_DAYS` (default 21). The first day it would go below zero is the danger day.

## Assumptions

- One private-bank account is the account that matters.
- A repeated card description is treated as monthly even when the gap is not a clean 30 days.
- Payday is a guess, not a salary contract.
- Pending and posted transactions are both eligible if the API returns them.
- No spend is labelled good or bad. Gym and sweets are both rocks.

## Install and run

Python 3.10 or newer. On 3.14, install `pygame-ce` (it imports as `pygame`).

```powershell
cd future-you
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m pytest -q
python main.py