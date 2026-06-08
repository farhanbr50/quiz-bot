# ... (Baaki code upar jaisa hai waisa hi rehne do, niche se replace karo)

# 3️⃣ Quiz Rokne Ka Command: /quiz/off
@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_native_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id]["active"]:
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("🛑 **Quiz ko beech mein hi rok diya gaya hai!**\n\nNaya game shuru karne ke liye `/quiz/on` likhein.")
    else:
        await message.answer("⚠️ **Abhi group mein koi quiz nahi chal raha hai jise roka jaye!**")

# 🌐 Webhook Handler
async def handle_webhook(request):
    url = str(request.url)
    if "webhook" in url:
        request_data = await request.json()
        update = types.Update(**request_data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    return web.Response(text="Bot Live!")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/", handle_webhook)
    
    if RENDER_URL:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url=f"{RENDER_URL}/webhook")

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(ma
                in())
