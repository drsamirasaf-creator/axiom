# ⭐ THE --forwarded-allow-ips FLAG BELOW IS INERT ON RAILWAY, AND THIS COMMENT
# EXISTS BECAUSE ITS ABSENCE MISLED. Railway ignores the Procfile and runs its
# own start command, so nothing written here governs production. Proxy header
# trust is set by the PLATFORM environment variable FORWARDED_ALLOW_IPS=* on the
# Railway service — see .env.example, "PLATFORM-ONLY" section.
#
# A rebuilder reading this line without the comment would conclude the problem
# is handled. It is handled somewhere the repository cannot see. Same defect
# class as shipped copy asserting something untrue: the text was correct as an
# intention and false as a description.
#
# The flag is retained so this file still works on a platform that DOES honour
# a Procfile (Heroku, Dokku, a local `honcho start`).
web: gunicorn services.api.main:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30 --forwarded-allow-ips="*"
