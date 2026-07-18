# Sprint 6 wires this into modal_app.py
# Cron schedule: 30 10 * * * (4:00 PM IST = 10:30 UTC)
#
# Sends quiz link emails to all students with an active learning plan.
# The quiz_results row was already created by morning_brief_cron.py at 7:30 AM.
# This cron generates the MCQs, fills in questions.items, and sends the link.
#
# Uncomment and integrate into modal_app.py during Sprint 6:
#
# import modal
# app = modal.App("skillbridge")
#
# @app.function(schedule=modal.Cron("30 10 * * *"))
# async def quiz_conductor_cron():
#     from src.agents.daily_checkin.quiz_conductor import send_links_for_all_users
#     await send_links_for_all_users()
