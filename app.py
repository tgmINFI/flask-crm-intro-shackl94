from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import Customer, Lead, Contact, Task, Appointment

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

def init_sample_data():
    Customer.add_customer('John Doe', 'john@example.com', 'Acme Corp', '555-0001', 'active')
    Customer.add_customer('Jane Smith', 'jane@example.com', 'Tech Solutions', '555-0002', 'prospect')
    Customer.add_customer('Bob Wilson', 'bob@example.com', 'Global Industries', '555-0003', 'inactive')
    Lead.add_lead('Alice Brown', 'alice@example.com', 'StartUp Inc', 50000, 'Website')
    Lead.add_lead('Charlie Davis', 'charlie@example.com', 'Enterprise Ltd', 100000, 'Referral')

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
        "status": getattr(l, "status", "new")
    }

def contact_to_dict(c):
    return {
        "id": c.id,
        "customer_id": c.customer_id,
        "contact_type": c.contact_type,
        "notes": c.notes
    }

@app.route('/')
def index():
    total_customers = len(Customer.get_all_customers())
    total_leads = len(Lead.get_all_leads())
    return render_template('index.html', total_customers=total_customers, total_leads=total_leads)

@app.route('/dashboard')
def dashboard():
    total_customers = len(Customer.get_all_customers())
    total_leads = len(Lead.get_all_leads())
    return render_template('index.html', total_customers=total_customers, total_leads=total_leads)

@app.route('/customers')
def customers():
    return render_template('customers.html', customers=Customer.get_all_customers())

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        phone = request.form.get('phone')
        status = request.form.get('status', 'prospect')

        if not all([name, email, company, phone]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_customer'))

        Customer.add_customer(name, email, company, phone, status)
        flash(f'Customer {name} added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('add_customer.html')

@app.route('/customers/<int:customer_id>')
def customer_detail(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    contacts = Contact.get_contacts_by_customer_id(customer_id)
    return render_template('customer_detail.html', customer=customer, contacts=contacts)

@app.route('/customers/<int:customer_id>/contacts/add', methods=['GET', 'POST'])
def add_contact(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        contact_type = request.form.get('contact_type')
        notes = request.form.get('notes')

        if not all([contact_type, notes]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_contact', customer_id=customer_id))

        Contact.add_contact(customer_id, contact_type, notes)
        flash('Contact added successfully!', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('add_contact.html', customer=customer)

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        Customer.update_customer(customer_id, request.form.get('name'), request.form.get('email'), 
                                request.form.get('company'), request.form.get('phone'), request.form.get('status'))
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))

    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    Customer.delete_customer(customer_id)
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/leads')
def leads():
    return render_template('leads.html', leads=Lead.get_all_leads())

@app.route('/leads/add', methods=['GET', 'POST'])
def add_lead():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        value = request.form.get('value')
        source = request.form.get('source')

        if not all([name, email, company, value, source]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_lead'))

        try:
            Lead.add_lead(name, email, company, float(value), source)
            flash(f'Lead {name} added successfully!', 'success')
        except ValueError:
            flash('Deal value must be a number!', 'error')

        return redirect(url_for('leads'))
    return render_template('add_lead.html')

@app.route('/leads/<int:lead_id>')
def lead_detail(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash('Lead not found!', 'error')
        return redirect(url_for('leads'))
    return render_template('lead_detail.html', lead=lead)

@app.route('/leads/<int:lead_id>/edit', methods=['GET', 'POST'])
def edit_lead(lead_id):
    lead = Lead.get_lead_by_id(lead_id)
    if not lead:
        flash('Lead not found!', 'error')
        return redirect(url_for('leads'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        value = request.form.get('value')
        source = request.form.get('source')
        status = request.form.get('status', lead.status)

        if not all([name, email, company, value, source]):
            flash('All fields are required!', 'error')
            return redirect(url_for('edit_lead', lead_id=lead_id))

        try:
            Lead.update_lead(lead_id, name, email, company, float(value), source, status)
            flash('Lead updated successfully!', 'success')
            return redirect(url_for('lead_detail', lead_id=lead_id))
        except ValueError:
            flash('Deal value must be a number!', 'error')
            return redirect(url_for('edit_lead', lead_id=lead_id))

    return render_template('edit_lead.html', lead=lead)

@app.route('/customers/<int:customer_id>/tasks/add', methods=['GET', 'POST'])
def add_task(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        due_date = request.form.get('due_date', '')

        if not title or not title.strip():
            flash('Title is required!', 'error')
            return redirect(url_for('add_task', customer_id=customer_id))

        Task.add_task(customer_id, title.strip(), description, due_date)
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks_for_customer', customer_id=customer_id))

    return render_template('add_task.html', customer=customer)

@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.get_task_by_id(task_id)
    if not task:
        flash('Task not found!', 'error')
        return redirect(url_for('customers'))

    customer = Customer.get_customer_by_id(task.customer_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        due_date = request.form.get('due_date', '')
        status = request.form.get('status', task.status)

        if not title or not title.strip():
            flash('Title is required!', 'error')
            return redirect(url_for('edit_task', task_id=task_id))

        Task.update_task(task_id, title.strip(), description, due_date, status)
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks_for_customer', customer_id=task.customer_id))

    return render_template('edit_task.html', task=task, customer=customer)

@app.route('/tasks/<int:task_id>/done', methods=['POST'])
def done_task(task_id):
    task = Task.get_task_by_id(task_id)
    if not task:
        flash('Task not found!', 'error')
        return redirect(url_for('customers'))

    Task.mark_done(task_id)
    flash('Task marked as done!', 'success')
    return redirect(url_for('tasks_for_customer', customer_id=task.customer_id))
@app.route('/customers/<int:customer_id>/appointments')
def appointments_for_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    appointments = Appointment.get_appointments_by_customer_id(customer_id)
    return render_template('appointments.html', customer=customer, appointments=appointments)
@app.route('/customers/<int:customer_id>/appointments/add', methods=['GET', 'POST'])
def add_appointment(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        start_datetime = request.form.get('start_datetime')
        end_datetime = request.form.get('end_datetime', '')
        notes = request.form.get('notes', '')

        if not start_datetime or not start_datetime.strip():
            flash('Start date/time is required!', 'error')
            return redirect(url_for('add_appointment', customer_id=customer_id))

        Appointment.add_appointment(customer_id, start_datetime.strip(), end_datetime.strip(), notes)
        flash('Appointment added successfully!', 'success')
        return redirect(url_for('appointments_for_customer', customer_id=customer_id))

    return render_template('add_appointment.html', customer=customer)
@app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    appointment = Appointment.get_appointment_by_id(appointment_id)
    if not appointment:
        flash('Appointment not found!', 'error')
        return redirect(url_for('customers'))

    customer = Customer.get_customer_by_id(appointment.customer_id)

    if request.method == 'POST':
        start_datetime = request.form.get('start_datetime')
        end_datetime = request.form.get('end_datetime', '')
        notes = request.form.get('notes', '')

        if not start_datetime or not start_datetime.strip():
            flash('Start date/time is required!', 'error')
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))

        Appointment.update_appointment(appointment_id, start_datetime.strip(), end_datetime.strip(), notes)
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments_for_customer', customer_id=appointment.customer_id))

    return render_template('edit_appointment.html', appointment=appointment, customer=customer)

@app.route('/leads/<int:lead_id>/delete', methods=['POST'])
def delete_lead(lead_id):
    Lead.delete_lead(lead_id)
    flash('Lead deleted successfully!', 'success')
    return redirect(url_for('leads'))

@app.route('/api/customers', methods=['GET'])
def api_get_customers():
    return jsonify([customer_to_dict(c) for c in Customer.get_all_customers()]), 200

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer_to_dict(c)), 200

@app.route('/api/customers', methods=['POST'])
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

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Felder aus JSON nehmen, wenn vorhanden, sonst bestehende Werte behalten
    name = data.get("name", c.name)
    email = data.get("email", c.email)
    company = data.get("company", c.company)
    phone = data.get("phone", c.phone)
    status = data.get("status", c.status)

    # Optional: minimale Validierung
    if not all([str(name).strip(), str(email).strip(), str(company).strip(), str(phone).strip()]):
        return jsonify({"error": "Missing required fields"}), 400

    Customer.update_customer(customer_id, name, email, company, phone, status)
    c_updated = Customer.get_customer_by_id(customer_id)
    return jsonify(customer_to_dict(c_updated)), 200
       
@app.route('/api/customers/<int:customer_id>/contacts', methods=['GET'])
def api_get_customer_contacts(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    contacts = Contact.get_contacts_by_customer_id(customer_id)
    return jsonify([contact_to_dict(x) for x in contacts]), 200

@app.route('/api/customers/<int:customer_id>/contacts', methods=['POST'])
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

@app.route('/customers/<int:customer_id>/tasks')
def tasks_for_customer(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))

    tasks = Task.get_tasks_by_customer_id(customer_id)
    return render_template('tasks.html', customer=customer, tasks=tasks)

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

@app.route('/api/customers/<int:customer_id>/tasks', methods=['GET'])
def api_get_tasks(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    tasks = Task.get_tasks_by_customer_id(customer_id)
    return jsonify([task_to_dict(t) for t in tasks]), 200

@app.route('/api/customers/<int:customer_id>/tasks', methods=['POST'])
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

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    t = Task.get_task_by_id(task_id)
    if not t:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = (data.get("title") or t.title).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    description = data.get("description", t.description)
    due_date = data.get("due_date", t.due_date)
    status = data.get("status", t.status)

    Task.update_task(task_id, title, description, due_date, status)
    t2 = Task.get_task_by_id(task_id)
    return jsonify(task_to_dict(t2)), 200

@app.route('/api/tasks/<int:task_id>/done', methods=['POST'])
def api_done_task(task_id):
    ok = Task.mark_done(task_id)
    if not ok:
        return jsonify({"error": "Task not found"}), 404
    t = Task.get_task_by_id(task_id)
    return jsonify(task_to_dict(t)), 200

@app.route('/api/customers/<int:customer_id>/appointments', methods=['GET'])
def api_get_appointments(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    apps = Appointment.get_appointments_by_customer_id(customer_id)
    return jsonify([appointment_to_dict(a) for a in apps]), 200

@app.route('/api/customers/<int:customer_id>/appointments', methods=['POST'])
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

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
def api_update_appointment(appointment_id):
    a = Appointment.get_appointment_by_id(appointment_id)
    if not a:
        return jsonify({"error": "Appointment not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    start_datetime = (data.get("start_datetime") or a.start_datetime).strip()
    if not start_datetime:
        return jsonify({"error": "start_datetime is required"}), 400

    end_datetime = (data.get("end_datetime") or a.end_datetime).strip()
    notes = data.get("notes", a.notes)

    Appointment.update_appointment(appointment_id, start_datetime, end_datetime, notes)
    a2 = Appointment.get_appointment_by_id(appointment_id)
    return jsonify(appointment_to_dict(a2)), 200

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    c = Customer.get_customer_by_id(customer_id)
    if not c:
        return jsonify({"error": "Customer not found"}), 404

    ok = Customer.delete_customer(customer_id)
    if not ok:
        return jsonify({"error": "Customer could not be deleted"}), 400

    return jsonify({"message": "Customer deleted"}), 200

@app.route('/api/leads', methods=['GET'])
def api_get_leads():
    return jsonify([lead_to_dict(l) for l in Lead.get_all_leads()]), 200

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def api_get_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404
    return jsonify(lead_to_dict(l)), 200

@app.route('/api/leads', methods=['POST'])
def api_create_lead():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required = ["name", "email", "company", "value", "source"]
    if not all(k in data and str(data[k]).strip() for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    status = data.get("status", "new")
    try:
        l = Lead.add_lead(data["name"], data["email"], data["company"], float(data["value"]), data["source"], status)
    except ValueError:
        return jsonify({"error": "Value must be a number"}), 400

    return jsonify(lead_to_dict(l)), 201

@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
def api_update_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = data.get("name", l.name)
    email = data.get("email", l.email)
    company = data.get("company", l.company)
    value = data.get("value", l.value)
    source = data.get("source", l.source)
    status = data.get("status", getattr(l, "status", "new"))

    try:
        Lead.update_lead(lead_id, name, email, company, float(value), source, status)
    except ValueError:
        return jsonify({"error": "Value must be a number"}), 400

    l_updated = Lead.get_lead_by_id(lead_id)
    return jsonify(lead_to_dict(l_updated)), 200

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def api_delete_lead(lead_id):
    l = Lead.get_lead_by_id(lead_id)
    if not l:
        return jsonify({"error": "Lead not found"}), 404

    ok = Lead.delete_lead(lead_id)
    if not ok:
        return jsonify({"error": "Lead could not be deleted"}), 400

    return jsonify({"message": "Lead deleted"}), 200

def task_to_dict(t):
    return {"id": t.id, "customer_id": t.customer_id, "title": t.title,
            "description": t.description, "due_date": t.due_date, "status": t.status}

def appointment_to_dict(a):
    return {"id": a.id, "customer_id": a.customer_id, "start_datetime": a.start_datetime,
            "end_datetime": a.end_datetime, "notes": a.notes}

@app.route('/api/customers/<int:customer_id>/tasks', methods=['GET'])
def api_get_tasks(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify([task_to_dict(t) for t in Task.get_tasks_by_customer_id(customer_id)]), 200

@app.route('/api/customers/<int:customer_id>/tasks', methods=['POST'])
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
    t = Task.add_task(customer_id, title, data.get("description",""), data.get("due_date",""))
    return jsonify(task_to_dict(t)), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(task_id):
    t = Task.get_task_by_id(task_id)
    if not t:
        return jsonify({"error": "Task not found"}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    title = (data.get("title") or t.title).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    Task.update_task(task_id, title, data.get("description", t.description),
                     data.get("due_date", t.due_date), data.get("status", t.status))
    return jsonify(task_to_dict(Task.get_task_by_id(task_id))), 200

@app.route('/api/tasks/<int:task_id>/done', methods=['POST'])
def api_done_task(task_id):
    ok = Task.mark_done(task_id)
    if not ok:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task_to_dict(Task.get_task_by_id(task_id))), 200


@app.route('/api/customers/<int:customer_id>/appointments', methods=['GET'])
def api_get_appointments(customer_id):
    customer = Customer.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify([appointment_to_dict(a) for a in Appointment.get_appointments_by_customer_id(customer_id)]), 200

@app.route('/api/customers/<int:customer_id>/appointments', methods=['POST'])
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
    a = Appointment.add_appointment(customer_id, start_datetime,
                                    (data.get("end_datetime") or "").strip(),
                                    data.get("notes",""))
    return jsonify(appointment_to_dict(a)), 201

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
def api_update_appointment(appointment_id):
    a = Appointment.get_appointment_by_id(appointment_id)
    if not a:
        return jsonify({"error": "Appointment not found"}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    start_datetime = (data.get("start_datetime") or a.start_datetime).strip()
    if not start_datetime:
        return jsonify({"error": "start_datetime is required"}), 400
    Appointment.update_appointment(appointment_id, start_datetime,
                                   (data.get("end_datetime") or a.end_datetime).strip(),
                                   data.get("notes", a.notes))
    return jsonify(appointment_to_dict(Appointment.get_appointment_by_id(appointment_id))), 200