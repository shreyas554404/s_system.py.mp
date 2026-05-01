import flask
from database import create_table, connect
from reportlab.pdfgen import canvas
from io import BytesIO

app = flask.Flask(__name__)
create_table()

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# HOME
@app.route("/")
def home():
    return flask.render_template("home.html")

# LOGIN
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    error = None
    if flask.request.method == "POST":
        user = flask.request.form["username"]
        pwd = flask.request.form["password"]

        if role == "admin":
            if user == ADMIN_USER and pwd == ADMIN_PASS:
                return flask.redirect("/admin")
            else:
                error = "Invalid admin credentials"
        else:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id=? AND password=?", (user, pwd))
            data = cursor.fetchone()
            conn.close()

            if data:
                return flask.redirect(f"/employee/{user}")
            else:
                error = "Invalid employee ID or password"

    return flask.render_template("login.html", role=role, error=error)

# ADMIN PANEL
@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = connect()
    cursor = conn.cursor()

    if flask.request.method == "POST":
        try:
            basic = float(flask.request.form["basic"])
            hra = float(flask.request.form["hra"])
            da = float(flask.request.form["da"])
            tax = float(flask.request.form["tax"])
            salary = basic + hra + da
            days = float(flask.request.form["days"])
            leaves = float(flask.request.form["leaves"])

            data = (
                flask.request.form["id"],
                flask.request.form["password"],
                flask.request.form["name"],
                flask.request.form["role"],
                salary,
                days,
                leaves,
                tax,
                float(flask.request.form["pf_amount"]),
                flask.request.form["pf_no"]
            )
            cursor.execute("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?)", data)
            conn.commit()
        except Exception:
            pass

    cursor.execute("SELECT id, name, role FROM employees")
    employees = cursor.fetchall()

    conn.close()

    return flask.render_template("admin.html", employees=employees)

# EMPLOYEE DASHBOARD
@app.route("/employee/<emp_id>")
def employee(emp_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        extra_leaves = max(0, data["leaves"] - 4)
        leave_deduction = extra_leaves * 1000
        tax_percent = data["tax"]
        tax_amount = data["salary"] * tax_percent / 100
        net_salary = data["salary"] - tax_amount - leave_deduction
    else:
        net_salary = None
        leave_deduction = 0
        tax_percent = 0
        tax_amount = 0

    return flask.render_template("employee.html", data=data, net_salary=net_salary, leave_deduction=leave_deduction, tax_percent=tax_percent, tax_amount=tax_amount)

# SALARY SLIP VIEW
@app.route("/slip/<emp_id>")
def slip(emp_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        extra_leaves = max(0, data["leaves"] - 4)
        leave_deduction = extra_leaves * 1000
        tax_percent = data["tax"]
        tax_amount = data["salary"] * tax_percent / 100
        net_salary = data["salary"] - tax_amount - leave_deduction
    else:
        net_salary = None
        leave_deduction = 0
        tax_percent = 0
        tax_amount = 0

    return flask.render_template("slip.html", data=data, net_salary=net_salary, leave_deduction=leave_deduction, tax_percent=tax_percent, tax_amount=tax_amount)

# PDF DOWNLOAD
@app.route("/download_pdf/<emp_id>")
def download_pdf(emp_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    data = cursor.fetchone()
    conn.close()

    if not data:
        return "Employee not found", 404

    extra_leaves = max(0, data["leaves"] - 4)
    leave_deduction = extra_leaves * 1000
    tax_percent = data["tax"]
    tax_amount = data["salary"] * tax_percent / 100
    net_salary = data["salary"] - tax_amount - leave_deduction

    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    c.drawString(150, 750, "SALARY SLIP")
    c.drawString(50, 700, f"Employee ID: {data['id']}")
    c.drawString(50, 680, f"Name: {data['name']}")
    c.drawString(50, 660, f"Role: {data['role']}")
    c.drawString(50, 640, f"Gross Salary: ₹{data['salary']:.2f}")
    c.drawString(50, 620, f"Working Days: {data['days']}")
    c.drawString(50, 600, f"Leaves: {data['leaves']}")
    c.drawString(50, 580, f"Tax: {tax_percent:.2f}% (₹{tax_amount:.2f})")
    c.drawString(50, 560, f"PF Amount: ₹{data['pf_amount']:.2f}")
    c.drawString(50, 540, f"PF No: {data['pf_no']}")
    c.drawString(50, 500, f"Net Salary: ₹{net_salary:.2f}")

    c.save()
    buffer.seek(0)

    return flask.send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"{data['name']}_salary.pdf")

if __name__ == "__main__":
    app.run(debug=True)