from flask import Flask, render_template, request, redirect, url_for, session
from database.connection import get_connection

app = Flask(__name__)
app.secret_key = "freshsip_secret_key_2026"

# ── Juice catalogue (single source of truth) ──────────────────────────────
JUICES = {
    "orange":     {"id": "orange",     "emoji": "🍊", "name": "Orange Burst",     "price": 79,  "tag": "Best Seller",   "color": "#FF6B2B", "description": "Freshly squeezed Valencia oranges bursting with Vitamin C. Bright, tangy, and naturally sweet — the perfect morning pick-me-up."},
    "mango":      {"id": "mango",      "emoji": "🥭", "name": "Mango Bliss",      "price": 99,  "tag": "Seasonal",      "color": "#FFC93C", "description": "Alphonso mangoes at peak ripeness, blended into a thick, golden nectar. Rich, fragrant, and utterly indulgent."},
    "strawberry": {"id": "strawberry", "emoji": "🍓", "name": "Strawberry Dream",  "price": 119, "tag": "Fan Favourite", "color": "#FF6B8A", "description": "Sun-ripened strawberries cold-pressed into a vibrant ruby juice. Delicate, floral, and full of antioxidants."},
    "grape":      {"id": "grape",      "emoji": "🍇", "name": "Grape Refresh",    "price": 89,  "tag": "Antioxidant",   "color": "#9B59B6", "description": "Deep purple Concord grapes pressed skin-on for maximum flavour and resveratrol. Earthy, rich, and deeply satisfying."},
    "pineapple":  {"id": "pineapple",  "emoji": "🍍", "name": "Pineapple Zing",   "price": 109, "tag": "Tropical",      "color": "#52C174", "description": "Golden pineapples from Tamil Nadu, cold-pressed for a fiercely tropical, enzyme-rich juice that aids digestion."},
    "lemon":      {"id": "lemon",      "emoji": "🍋", "name": "Lemon Detox",      "price": 69,  "tag": "Detox",         "color": "#E8D44D", "description": "Sicilian lemons with a hint of ginger and mint. Zingy, cleansing, and the best liver-reset in a bottle."},
    "watermelon": {"id": "watermelon", "emoji": "🍉", "name": "Watermelon Chill", "price": 89,  "tag": "Summer Hit",    "color": "#FF4757", "description": "Seedless watermelons spun into a light, hydrating cooler. 92% water, 100% refreshing — perfect for hot Hyderabad days."},
    "apple":      {"id": "apple",      "emoji": "🍏", "name": "Apple Crisp",      "price": 79,  "tag": "Classic",       "color": "#2ECC71", "description": "Granny Smith and Fuji apples blended together for a balanced, crisp juice that never goes out of style."},
}

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM user_credentials
            WHERE username = ?
            AND password_hash = ?
        """,
        (
            username,
            password
        ))

        user = cursor.fetchone()

        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html",
                error="Invalid username or password"
            )

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone_number = request.form["phone"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        # Check username exists
        cursor.execute(
            "SELECT * FROM user_credentials WHERE username=?",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template("signup.html", error="Username already exists")

        # 1. Insert into signup_page_details
        cursor.execute("""
            INSERT INTO signup_page_details
            (first_name, middle_name, last_name, email, phone_number)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?)
        """,
        (first_name, middle_name, last_name, email, phone_number))

        # 2. Get inserted ID
        # cursor.execute("SELECT SCOPE_IDENTITY()")
        user_id = cursor.fetchone()[0]

        # 3. Insert into credentials
        cursor.execute("""
            INSERT INTO user_credentials
            (user_id, username, password_hash)
            VALUES (?, ?, ?)
        """,
        (user_id, username, password))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username     = request.form["username"]
        # old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        re_new_password = request.form["re_new_password"]

        # 1. New passwords must match
        if new_password != re_new_password:
            return render_template(
                "forgot_password.html",
                error="New passwords do not match. Please try again."
            )

        # 2. New password must differ from old
        # if new_password == old_password:
        #     return render_template(
        #         "forgot_password.html",
        #         error="New password must be different from the old password."
        #     )

        conn   = get_connection()
        cursor = conn.cursor()

        # 3. Verify username + old password exist
        cursor.execute("""
            SELECT *
            FROM user_credentials
            WHERE username      = ?
        """, (username))

        user = cursor.fetchone()

        if not user:
            conn.close()
            return render_template(
                "forgot_password.html",
                error="Username or old password is incorrect."
            )

        # 4. Update password_hash with the new password
        cursor.execute("""
            UPDATE user_credentials
            SET    password_hash = ?
            WHERE  username      = ?
        """, (new_password, username))

        conn.commit()
        conn.close()

        return render_template(
            "forgot_password.html",
            success="Password updated successfully! You can now log in."
        )

    return render_template("forgot_password.html")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)