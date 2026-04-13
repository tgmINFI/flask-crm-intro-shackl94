from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from sqlalchemy import or_

from models import db, User, Customer, Lead, Contact, Task, Appointment

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crm.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
    


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required"}), 401
    flash("Bitte zuerst einloggen.", "warning")
    return redirect(url_for("login"))


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("login"))

            if current_user.role != role:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden"}), 403
                flash("Zugriff verweigert.", "danger")
                return redirect(url_for("index"))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def init_sample_data():
    if Customer.query.count() == 0:
        Customer.add_customer("John Doe", "john@example.com", "Acme Corp", "555-0001", "active")
        Customer.add_customer("Jane Smith", "jane@example.com", "Tech Solutions", "555-0002", "prospect")
        Customer.add_customer("Bob Wilson", "bob@example.com", "Global Industries", "555-0003", "inactive")

    if Lead.query.count() == 0:
        Lead.add_lead("Alice Brown", "alice@example.com", "StartUp Inc", 50000, "Website", "new")
        Lead.add_lead("Charlie Davis", "charlie@example.com", "Enterprise Ltd", 100000, "Referral", "qualified")

    if User.query.count() == 0:
        admin = User(username="admin", email="admin@example.com", role="admin")
        admin.set_password("admin123")

        user = User(username="user", email="user@example.com", role="user")
        user.set_password("user123")

        db.session.add(admin)
        db.session.add(user)
        db.session.commit()


with app.app_context():
    db.create_all()
    init_sample_data()


def customer_to_dict(c):
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "company": c.company,
        "phone": c.phone,
        "status": c.status
    }


def lead_to_dict(l):
    return {
        "id": l.id,
        "name": l.name,
        "email": l.email,
        "company": l.company,
        "value": l.value,
        "source": l.source,
        "status": l.status
    }


def contact_to_dict(c):
    return {
        "id": c.id,
        "customer_id": c.customer_id,
        "contact_type": c.contact_type,
        "notes": c.notes
    }


def task_to_dict(t):
    return {
        "id": t.id,
        "customer_id": t.customer_id,
        "title": t.title,
        "description": t.description,
        "due_date": t.due_date,
        "status": t.status
    }


def appointment_to_dict(a):
    return {
        "id": a.id,
        "customer_id": a.customer_id,
        "start_datetime": a.start_datetime,
        "end_datetime": a.end_datetime,
        "notes": a.notes
    }


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("Alle Felder sind erforderlich.", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()

        if existing_user:
            flash("Benutzername oder E-Mail existiert bereits.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registrierung erfolgreich. Bitte einloggen.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login erfolgreich.", "success")
            return redirect(url_for("index"))

        flash("Ungültige Zugangsdaten.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Erfolgreich ausgeloggt.", "success")
    return redirect(url_for("login"))

@app.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
@role_required("admin")
def change_user_role(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("admin_users"))

    new_role = request.form.get("role", "").strip().lower()

    if new_role not in ["admin", "user"]:
        flash("Ungültige Rolle.", "danger")
        return redirect(url_for("admin_users"))

    user.role = new_role
    db.session.commit()

    flash(f"Rolle von {user.username} wurde auf {new_role} geändert.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("admin_users"))

    if user.id == current_user.id:
        flash("Du kannst deinen eigenen Admin-Account nicht löschen.", "danger")
        return redirect(url_for("admin_users"))

    db.session.delete(user)
    db.session.commit()

    flash("Benutzer gelöscht.", "success")
    return redirect(url_for("admin_users"))

@app.route("/")
@login_required
def index():
    total_customers = len(Customer.get_all_customers())
    total_leads = len(Lead.get_all_leads())
    return render_template("index.html", total_customers=total_customers, total_leads=total_leads)


@app.route("/dashboard")
@login_required
def dashboard():
    total_customers = len(Customer.get_all_customers())
    total_leads = len(Lead.get_all_leads())
    return render_template("index.html", total_customers=total_customers, total_leads=total_leads)


@app.route("/customers")
@login_required
def customers():
    return render_template("customers.html", customers=Customer.get_all_customers())


@app.route("/customers/add", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        phone = request.form.get("phone", "").strip()
        status = request.form.get("status", "prospect").strip()

        if not all([name, email, company, phone]):
            flash("All fields are required!", "danger")
            return redirect(url_for("add_customer"))

        Customer.add_customer(name, email, company, phone, status)
        flash(f"Customer {name} added successfully!", "success")
        return redirect(url_for("customers"))

    return render_template("add_customer.html")


@app.route("/customers/<int:customer_id>")
@login_required
def customer_detail(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    contacts = Contact.get_contacts_by_customer_id(customer_id)
    return render_template("customer_detail.html", customer=customer, contacts=contacts)


@app.route("/customers/<int:customer_id>/contacts/add", methods=["GET", "POST"])
@login_required
def add_contact(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        contact_type = request.form.get("contact_type", "").strip()
        notes = request.form.get("notes", "").strip()

        if not all([contact_type, notes]):
            flash("All fields are required!", "danger")
            return redirect(url_for("add_contact", customer_id=customer_id))

        Contact.add_contact(customer_id, contact_type, notes)
        flash("Contact added successfully!", "success")
        return redirect(url_for("customer_detail", customer_id=customer_id))

    return render_template("add_contact.html", customer=customer)


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        Customer.update_customer(
            customer_id,
            request.form.get("name", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("company", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("status", "prospect").strip()
        )
        flash("Customer updated successfully!", "success")
        return redirect(url_for("customer_detail", customer_id=customer_id))

    return render_template("edit_customer.html", customer=customer)


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_customer(customer_id):
    Customer.delete_customer(customer_id)
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


@app.route("/leads")
@login_required
def leads():
    return render_template("leads.html", leads=Lead.get_all_leads())


@app.route("/leads/add", methods=["GET", "POST"])
@login_required
def add_lead():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        value = request.form.get("value", "").strip()
        source = request.form.get("source", "").strip()

        if not all([name, email, company, value, source]):
            flash("All fields are required!", "danger")
            return redirect(url_for("add_lead"))

        try:
            Lead.add_lead(name, email, company, float(value), source)
            flash(f"Lead {name} added successfully!", "success")
        except ValueError:
            flash("Deal value must be a number!", "danger")

        return redirect(url_for("leads"))

    return render_template("add_lead.html")


@app.route("/leads/<int:lead_id>")
@login_required
def lead_detail(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash("Lead not found!", "danger")
        return redirect(url_for("leads"))
    return render_template("lead_detail.html", lead=lead)


@app.route("/leads/<int:lead_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lead(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash("Lead not found!", "danger")
        return redirect(url_for("leads"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        value = request.form.get("value", "").strip()
        source = request.form.get("source", "").strip()
        status = request.form.get("status", lead.status).strip()

        if not all([name, email, company, value, source]):
            flash("All fields are required!", "danger")
            return redirect(url_for("edit_lead", lead_id=lead_id))

        try:
            Lead.update_lead(lead_id, name, email, company, float(value), source, status)
            flash("Lead updated successfully!", "success")
            return redirect(url_for("lead_detail", lead_id=lead_id))
        except ValueError:
            flash("Deal value must be a number!", "danger")
            return redirect(url_for("edit_lead", lead_id=lead_id))

    return render_template("edit_lead.html", lead=lead)


@app.route("/leads/<int:lead_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_lead(lead_id):
    Lead.delete_lead(lead_id)
    flash("Lead deleted successfully!", "success")
    return redirect(url_for("leads"))


@app.route("/customers/<int:customer_id>/tasks")
@login_required
def tasks_for_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    tasks = Task.get_tasks_by_customer_id(customer_id)
    return render_template("tasks.html", customer=customer, tasks=tasks)


@app.route("/customers/<int:customer_id>/tasks/add", methods=["GET", "POST"])
@login_required
def add_task(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        due_date = request.form.get("due_date", "")

        if not title:
            flash("Title is required!", "danger")
            return redirect(url_for("add_task", customer_id=customer_id))

        Task.add_task(customer_id, title, description, due_date)
        flash("Task added successfully!", "success")
        return redirect(url_for("tasks_for_customer", customer_id=customer_id))

    return render_template("add_task.html", customer=customer)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.get_task_by_id(task_id)
    if not task:
        flash("Task not found!", "danger")
        return redirect(url_for("customers"))

    customer = Customer.get_customer_by_id(task.customer_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        due_date = request.form.get("due_date", "")
        status = request.form.get("status", task.status)

        if not title:
            flash("Title is required!", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        Task.update_task(task_id, title, description, due_date, status)
        flash("Task updated successfully!", "success")
        return redirect(url_for("tasks_for_customer", customer_id=task.customer_id))

    return render_template("edit_task.html", task=task, customer=customer)


@app.route("/tasks/<int:task_id>/done", methods=["POST"])
@login_required
def done_task(task_id):
    task = Task.get_task_by_id(task_id)
    if not task:
        flash("Task not found!", "danger")
        return redirect(url_for("customers"))

    Task.mark_done(task_id)
    flash("Task marked as done!", "success")
    return redirect(url_for("tasks_for_customer", customer_id=task.customer_id))


@app.route("/customers/<int:customer_id>/appointments")
@login_required
def appointments_for_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    appointments = Appointment.get_appointments_by_customer_id(customer_id)
    return render_template("appointments.html", customer=customer, appointments=appointments)


@app.route("/customers/<int:customer_id>/appointments/add", methods=["GET", "POST"])
@login_required
def add_appointment(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash("Customer not found!", "danger")
        return redirect(url_for("customers"))

    if request.method == "POST":
        start_datetime = request.form.get("start_datetime", "").strip()
        end_datetime = request.form.get("end_datetime", "").strip()
        notes = request.form.get("notes", "")

        if not start_datetime:
            flash("Start date/time is required!", "danger")
            return redirect(url_for("add_appointment", customer_id=customer_id))

        Appointment.add_appointment(customer_id, start_datetime, end_datetime, notes)
        flash("Appointment added successfully!", "success")
        return redirect(url_for("appointments_for_customer", customer_id=customer_id))

    return render_template("add_appointment.html", customer=customer)


@app.route("/appointments/<int:appointment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.get_appointment_by_id(appointment_id)
    if not appointment:
        flash("Appointment not found!", "danger")
        return redirect(url_for("customers"))

    customer = Customer.get_customer_by_id(appointment.customer_id)

    if request.method == "POST":
        start_datetime = request.form.get("start_datetime", "").strip()
        end_datetime = request.form.get("end_datetime", "").strip()
        notes = request.form.get("notes", "")

        if not start_datetime:
            flash("Start date/time is required!", "danger")
            return redirect(url_for("edit_appointment", appointment_id=appointment_id))

        Appointment.update_appointment(appointment_id, start_datetime, end_datetime, notes)
        flash("Appointment updated successfully!", "success")
        return redirect(url_for("appointments_for_customer", customer_id=appointment.customer_id))

    return render_template("edit_appointment.html", appointment=appointment, customer=customer)

# Diese Route definiert eine URL im Webserver.
# Wenn jemand im Browser /api/docs aufruft,
# wird die Funktion api_docs() ausgeführt. Damit kann leichter nochvollzogen werden,welche apis existieren.
@app.route("/api/docs")
def api_docs():
    return jsonify({
        # Allgemeine Beschreibung der API
        "description": "CRM REST API",
        "authentication": "Session-based login required for protected endpoints",
        # Hier werden die verschiedenen API-Endpunkte dokumentiert.
        "endpoints": {
            # Beschreibung der Customer API
            "customers": {
                "GET /api/customers": "Alle Kunden abrufen",
                "GET /api/customers/<id>": "Einen Kunden abrufen",
                "POST /api/customers": "Neuen Kunden anlegen",
                "PUT /api/customers/<id>": "Kunden aktualisieren",
                "DELETE /api/customers/<id>": "Kunden löschen (Admin)"
            },
            # Beschreibung der Kontakte
            "contacts": {
                "GET /api/customers/<customer_id>/contacts": "Kontakte eines Kunden abrufen",
                "POST /api/customers/<customer_id>/contacts": "Kontakt anlegen"
            },
            # Beschreibung der Leads API
            "leads": {
                "GET /api/leads": "Alle Leads abrufen",
                "GET /api/leads/<id>": "Einen Lead abrufen",
                "POST /api/leads": "Lead anlegen",
                "PUT /api/leads/<id>": "Lead aktualisieren",
                "DELETE /api/leads/<id>": "Lead löschen (Admin)"
            },
            # Beschreibung der Tasks API
            "tasks": {
                "GET /api/customers/<customer_id>/tasks": "Tasks eines Kunden abrufen",
                "POST /api/customers/<customer_id>/tasks": "Task anlegen",
                "PUT /api/tasks/<id>": "Task aktualisieren",
                "POST /api/tasks/<id>/done": "Task als erledigt markieren"
            },
            # Beschreibung der Appointment API
            "appointments": {
                "GET /api/customers/<customer_id>/appointments": "Termine eines Kunden abrufen",
                "POST /api/customers/<customer_id>/appointments": "Termin anlegen",
                "PUT /api/appointments/<id>": "Termin aktualisieren"
            }
        }
    })


@app.route("/api/customers", methods=["GET"])
@login_required
def api_get_customers():
    return jsonify([customer_to_dict(c) for c in Customer.get_all_customers()]), 200


@app.route("/api/customers/<int:customer_id>", methods=["GET"])
@login_required
def api_get_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer_to_dict(c)), 200


@app.route("/api/customers", methods=["POST"])
@login_required
def api_create_customer():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["name", "email", "company", "phone"]
    if not all(k in data and str(data[k]).strip() for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    status = data.get("status", "prospect")
    c = Customer.add_customer(data["name"], data["email"], data["company"], data["phone"], status)
    return jsonify(customer_to_dict(c)), 201


@app.route("/api/customers/<int:customer_id>", methods=["PUT"])
@login_required
def api_update_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = str(data.get("name", c.name)).strip()
    email = str(data.get("email", c.email)).strip()
    company = str(data.get("company", c.company)).strip()
    phone = str(data.get("phone", c.phone)).strip()
    status = str(data.get("status", c.status)).strip()

    if not all([name, email, company, phone]):
        return jsonify({"error": "Missing required fields"}), 400

    Customer.update_customer(customer_id, name, email, company, phone, status)
    updated = Customer.get_customer_by_id(customer_id)
    return jsonify(customer_to_dict(updated)), 200


@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
@login_required
@role_required("admin")
def api_delete_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    ok = Customer.delete_customer(customer_id)
    if not ok:
        return jsonify({"error": "Customer could not be deleted"}), 400

    return jsonify({"message": "Customer deleted"}), 200


@app.route("/api/customers/<int:customer_id>/contacts", methods=["GET"])
@login_required
def api_get_customer_contacts(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    contacts = Contact.get_contacts_by_customer_id(customer_id)
    return jsonify([contact_to_dict(x) for x in contacts]), 200


@app.route("/api/customers/<int:customer_id>/contacts", methods=["POST"])
@login_required
def api_create_customer_contact(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["contact_type", "notes"]
    if not all(k in data and str(data[k]).strip() for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    contact = Contact.add_contact(customer_id, data["contact_type"], data["notes"])
    return jsonify(contact_to_dict(contact)), 201


@app.route("/api/leads", methods=["GET"])
@login_required
def api_get_leads():
    return jsonify([lead_to_dict(l) for l in Lead.get_all_leads()]), 200


@app.route("/api/leads/<int:lead_id>", methods=["GET"])
@login_required
def api_get_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404
    return jsonify(lead_to_dict(l)), 200


@app.route("/api/leads", methods=["POST"])
@login_required
def api_create_lead():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["name", "email", "company", "value", "source"]
    if not all(k in data and str(data[k]).strip() for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    status = data.get("status", "new")

    try:
        l = Lead.add_lead(
            data["name"],
            data["email"],
            data["company"],
            float(data["value"]),
            data["source"],
            status
        )
    except ValueError:
        return jsonify({"error": "Value must be a number"}), 400

    return jsonify(lead_to_dict(l)), 201


@app.route("/api/leads/<int:lead_id>", methods=["PUT"])
@login_required
def api_update_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = str(data.get("name", l.name)).strip()
    email = str(data.get("email", l.email)).strip()
    company = str(data.get("company", l.company)).strip()
    source = str(data.get("source", l.source)).strip()
    status = str(data.get("status", l.status)).strip()
    value_raw = data.get("value", l.value)

    if not all([name, email, company, source]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        value = float(value_raw)
        Lead.update_lead(lead_id, name, email, company, value, source, status)
    except ValueError:
        return jsonify({"error": "Value must be a number"}), 400

    updated = Lead.get_lead_by_id(lead_id)
    return jsonify(lead_to_dict(updated)), 200


@app.route("/api/leads/<int:lead_id>", methods=["DELETE"])
@login_required
@role_required("admin")
def api_delete_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404

    ok = Lead.delete_lead(lead_id)
    if not ok:
        return jsonify({"error": "Lead could not be deleted"}), 400

    return jsonify({"message": "Lead deleted"}), 200


@app.route("/api/customers/<int:customer_id>/tasks", methods=["GET"])
@login_required
def api_get_tasks(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    tasks = Task.get_tasks_by_customer_id(customer_id)
    return jsonify([task_to_dict(t) for t in tasks]), 200


@app.route("/api/customers/<int:customer_id>/tasks", methods=["POST"])
@login_required
def api_create_task(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    description = data.get("description", "")
    due_date = data.get("due_date", "")

    t = Task.add_task(customer_id, title, description, due_date)
    return jsonify(task_to_dict(t)), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def api_update_task(task_id):
    t = Task.get_task_by_id(task_id)
    if not t:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = str(data.get("title", t.title)).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    description = data.get("description", t.description)
    due_date = data.get("due_date", t.due_date)
    status = data.get("status", t.status)

    Task.update_task(task_id, title, description, due_date, status)
    updated = Task.get_task_by_id(task_id)
    return jsonify(task_to_dict(updated)), 200


@app.route("/api/tasks/<int:task_id>/done", methods=["POST"])
@login_required
def api_done_task(task_id):
    ok = Task.mark_done(task_id)
    if not ok:
        return jsonify({"error": "Task not found"}), 404

    t = Task.get_task_by_id(task_id)
    return jsonify(task_to_dict(t)), 200


@app.route("/api/customers/<int:customer_id>/appointments", methods=["GET"])
@login_required
def api_get_appointments(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    apps = Appointment.get_appointments_by_customer_id(customer_id)
    return jsonify([appointment_to_dict(a) for a in apps]), 200


@app.route("/api/customers/<int:customer_id>/appointments", methods=["POST"])
@login_required
def api_create_appointment(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    start_datetime = (data.get("start_datetime") or "").strip()
    if not start_datetime:
        return jsonify({"error": "start_datetime is required"}), 400

    end_datetime = (data.get("end_datetime") or "").strip()
    notes = data.get("notes", "")

    a = Appointment.add_appointment(customer_id, start_datetime, end_datetime, notes)
    return jsonify(appointment_to_dict(a)), 201


@app.route("/api/appointments/<int:appointment_id>", methods=["PUT"])
@login_required
def api_update_appointment(appointment_id):
    a = Appointment.get_appointment_by_id(appointment_id)
    if not a:
        return jsonify({"error": "Appointment not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    start_datetime = str(data.get("start_datetime", a.start_datetime)).strip()
    if not start_datetime:
        return jsonify({"error": "start_datetime is required"}), 400

    end_datetime = str(data.get("end_datetime", a.end_datetime)).strip()
    notes = data.get("notes", a.notes)

    Appointment.update_appointment(appointment_id, start_datetime, end_datetime, notes)
    updated = Appointment.get_appointment_by_id(appointment_id)
    return jsonify(appointment_to_dict(updated)), 200


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)