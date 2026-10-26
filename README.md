# LeetCode Daily Reminder

A lightweight Python Telegram bot that reminds you to solve at least one LeetCode problem every day. It checks recent public Accepted submissions, so any LeetCode problem counts—not just the Daily Challenge.

**No database. No LeetCode password. Just a simple daily coding habit.**

[Documentation](https://koraleetcode.vercel.app/) · [GitHub Repository](https://github.com/AravindisDev/LeetCodeReminder)

## Features

- 🎯 **Daily goal tracking** — Any accepted LeetCode problem counts.
- 🔔 **Telegram reminders** — Get reminded when you haven't solved a problem today.
- 🇮🇳 **IST support** — Uses `Asia/Kolkata` by default.
- ⏰ **Built-in scheduler** — Checks reminder slots automatically without GitHub Actions.
- ☁️ **Flexible hosting** — Deploy on Railway, Render, or your own VPS.
- 🔐 **Protected endpoint** — Manual reminder checks require a secret token.
- 🪶 **Lightweight** — Uses Python's standard library without a database.
- 🌍 **Open source** — Released under the MIT License.

## How It Works

1. The Python service runs continuously on your hosting platform.
2. Its built-in scheduler checks during the first five minutes of each half-hour slot.
3. It checks your 20 most recent public Accepted LeetCode submissions.
4. If you have solved a problem today, no reminder is sent.
5. If you haven't solved one and a reminder slot is active, the bot sends a Telegram message.

The service also provides a `/health` endpoint for health checks and an authenticated `/api/check` endpoint for manual checks.

## Reminder Schedule

By default, reminders are eligible during these windows in `Asia/Kolkata` time:

- 3:00–3:04 PM
- 3:30–3:34 PM
- 4:00–4:04 PM
- Every half hour after that
- Final slot: 11:30–11:34 PM

The scheduler checks every 20 seconds while the service is running.

**Important:** The service must remain running for automatic reminders to work. Hosting platforms may restart or sleep services, which can affect reminder delivery. Render's free web services may spin down when idle, so an always-on service or VPS is recommended.

## Tech Stack

- **Python** — Application and scheduler
- **LeetCode GraphQL interface** — Public submission lookup
- **Telegram Bot API** — Reminder delivery
- **Railway / Render / VPS** — Hosting options
- **Docker** — Optional container deployment

## Project Structure

```text
LeetCodeReminder/
├── app.py
├── Dockerfile
├── Procfile
├── render.yaml
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/AravindisDev/LeetCodeReminder.git
cd LeetCodeReminder
```

Make sure Python 3.12 or newer is installed if you plan to run the service locally or on a VPS.

### 2. Create a Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`.
3. Follow the instructions to create your bot.
4. Copy the bot token and keep it private.

### 3. Get Your Telegram Chat ID

You can use the Rose bot to find your chat ID:

1. Open Telegram and find Rose.
2. Start a conversation with Rose or add it to your target group.
3. Send `/id`.
4. Copy the returned chat ID.
5. Use it as `TELEGRAM_CHAT_ID`.

If you want group reminders, add your reminder bot to the group and make sure it can send messages.

### 4. Configure Environment Variables

Add these variables in your hosting provider's environment-variable settings.

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat or group ID |
| `LEETCODE_USERNAME` | Your public LeetCode username |
| `CRON_SECRET` | A long, random secret for the manual check endpoint |
| `TIMEZONE` | Timezone; defaults to `Asia/Kolkata` |
| `PORT` | Port provided by the hosting platform; defaults to `8080` |

Example configuration:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
LEETCODE_USERNAME=your_leetcode_username
CRON_SECRET=replace_with_a_long_random_secret
TIMEZONE=Asia/Kolkata
PORT=8080
```

Replace the example values with your own. Do not commit real credentials to GitHub.

### 5. Deploy on Railway

1. Push the project to GitHub.
2. Create a project on [Railway](https://railway.app/).
3. Deploy the project from your GitHub repository.
4. Add the environment variables in the service's Variables settings.
5. Set the start command to `python app.py` if it isn't detected automatically.
6. Deploy and check the service logs.

Open the following URL using your Railway domain:

```text
https://YOUR-DOMAIN/health
```

A successful health check returns a JSON response similar to:

```json
{
  "ok": true,
  "service": "leetcode-reminder"
}
```

Check Railway's current pricing and usage limits before deploying.

### 6. Deploy on Render

1. Create a **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Set the build command to:

```bash
pip install -r requirements.txt
```

4. Set the start command to:

```bash
python app.py
```

5. Add all required environment variables.
6. Deploy the service and test its `/health` endpoint.

**Note:** Render free web services may sleep when idle. Since this project relies on a continuously running scheduler, use an always-on service for more reliable reminders.

### 7. Run on a VPS or Locally

Install Python 3.12 or newer, clone the repository, and configure the environment variables.

Start the service with:

```bash
python app.py
```

Keep the process running. On a VPS, use a process manager such as `systemd` or Docker to restart the application after a reboot or failure.

A `Dockerfile` is included if you prefer container deployment.

## Testing the Service

### Health Check

Open:

```text
https://YOUR-DOMAIN/health
```

This checks whether the web server is responding.

### Manual Reminder Check

Use the following URL:

```text
https://YOUR-DOMAIN/api/check?token=YOUR_CRON_SECRET
```

Replace the placeholders with your deployed domain and actual secret.

Possible responses include:

- `sent` — A reminder was sent.
- `skip` — No reminder was needed or the current time is outside a reminder window.
- `401 Unauthorized` — The secret token is missing or incorrect.
- `502 Bad Gateway` — An external API request failed.
- `500 Internal Server Error` — An unexpected server error occurred.

**Security:** The manual-check URL contains your secret token. Do not share it publicly or commit it to GitHub.

## Limitations

- LeetCode's public GraphQL interface is unofficial and may change.
- The checker looks at up to 20 recent public Accepted submissions.
- Private submissions are not accessed, and no LeetCode password is required.
- No database is used, so a restart may cause a reminder slot to be processed again.
- Only one scheduler process should run for a deployment to avoid duplicate reminders.
- Hosting availability and external API failures can affect delivery.
- This project is not affiliated with or endorsed by LeetCode, Telegram, Railway, Render, or GitHub.

## Contributing

Contributions, bug reports, and feature suggestions are welcome!

1. Fork the repository.
2. Create a branch for your changes.
3. Make and test your changes.
4. Open a pull request describing your improvement.

Never include real API tokens or other private credentials in a pull request.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Author

**AravindisDev**

- GitHub: [@AravindisDev](https://github.com/AravindisDev)
- Repository: [AravindisDev/LeetCodeReminder](https://github.com/AravindisDev/LeetCodeReminder)
- Documentation: [koraleetcode.vercel.app](https://koraleetcode.vercel.app/)

---

If this project helps you stay consistent with coding practice, consider giving the repository a ⭐.
