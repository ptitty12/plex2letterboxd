from flask import Flask, render_template, request, send_file
from plexapi.server import PlexServer
from datetime import datetime
import csv
import io

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
BASEURL = "http://99.97.137.87:32400"
TOKEN = "cwL3SnPsbL4hj__GgBiE"
LIBRARY_NAME = "Tower Movies"

# -------------------------
# HELPERS
# -------------------------
def get_external_ids(movie):
    imdb_id = None
    tmdb_id = None

    for guid in (g.id for g in movie.guids):
        if guid.startswith("imdb://"):
            imdb_id = guid.replace("imdb://", "")
        elif guid.startswith("tmdb://"):
            tmdb_id = guid.replace("tmdb://", "")

    return imdb_id, tmdb_id


def get_users():
    plex = PlexServer(BASEURL, TOKEN)
    account = plex.myPlexAccount()

    users = []

    # Always include the owner account
    users.append({
        "username": plex.account().username
    })

    # Include ONLY non-managed users
    for user in account.users():
        if user.home:
            continue  # skip managed users

        users.append({
            "username": user.username
        })

    return users



def export_csv(username):
    plex = PlexServer(BASEURL, TOKEN)
    account = plex.myPlexAccount()

    if username != plex.account().username:
        user = account.user(username)
        token = user.get_token(plex.machineIdentifier)
        plex = PlexServer(BASEURL, token)

    section = plex.library.section(LIBRARY_NAME)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Title",
        "Year",
        "imdbID",
        "tmdbID",
        "Rating10",
        "WatchedDate"
    ])

    for movie in section.search(unwatched=False, sort="lastViewedAt"):
        imdbID, tmdbID = get_external_ids(movie)

        watched_date = (
            movie.lastViewedAt.strftime("%Y-%m-%d")
            if movie.lastViewedAt else None
        )

        rating = (
            f"{movie.userRating:.0f}"
            if movie.userRating is not None else None
        )

        writer.writerow([
            movie.title,
            movie.year,
            imdbID,
            tmdbID,
            rating,
            watched_date
        ])

    output.seek(0)
    return output


# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def index():
    users = get_users()
    return render_template("index.html", users=users)


@app.route("/export", methods=["POST"])
def export():
    username = request.form.get("username")

    if not username:
        return "No user selected", 400

    csv_data = export_csv(username)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{username}_{today}_watched_movies.csv"

    return send_file(
        io.BytesIO(csv_data.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run()
