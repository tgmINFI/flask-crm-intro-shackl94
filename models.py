from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="prospect")

    contacts = db.relationship(
        "Contact",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True
    )
    tasks = db.relationship(
        "Task",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True
    )
    appointments = db.relationship(
        "Appointment",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True
    )

    @classmethod
    def add_customer(cls, name, email, company, phone, status="prospect"):
        customer = cls(
            name=name,
            email=email,
            company=company,
            phone=phone,
            status=status
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @classmethod
    def get_all_customers(cls):
        return cls.query.order_by(cls.id.asc()).all()

    @classmethod
    def get_customer_by_id(cls, customer_id):
        return cls.query.get(customer_id)

    @classmethod
    def update_customer(cls, customer_id, name, email, company, phone, status):
        customer = cls.get_customer_by_id(customer_id)
        if customer:
            customer.name = name
            customer.email = email
            customer.company = company
            customer.phone = phone
            customer.status = status
            db.session.commit()
        return customer

    @classmethod
    def delete_customer(cls, customer_id):
        customer = cls.get_customer_by_id(customer_id)
        if customer:
            db.session.delete(customer)
            db.session.commit()
            return True
        return False


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="new")

    @classmethod
    def add_lead(cls, name, email, company, value, source, status="new"):
        lead = cls(
            name=name,
            email=email,
            company=company,
            value=value,
            source=source,
            status=status
        )
        db.session.add(lead)
        db.session.commit()
        return lead

    @classmethod
    def get_all_leads(cls):
        return cls.query.order_by(cls.id.asc()).all()

    @classmethod
    def get_lead_by_id(cls, lead_id):
        return cls.query.get(lead_id)

    @classmethod
    def update_lead(cls, lead_id, name, email, company, value, source, status=None):
        lead = cls.get_lead_by_id(lead_id)
        if lead:
            lead.name = name
            lead.email = email
            lead.company = company
            lead.value = value
            lead.source = source
            if status is not None:
                lead.status = status
            db.session.commit()
        return lead

    @classmethod
    def delete_lead(cls, lead_id):
        lead = cls.get_lead_by_id(lead_id)
        if lead:
            db.session.delete(lead)
            db.session.commit()
            return True
        return False


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    contact_type = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.Text, nullable=False)

    @classmethod
    def add_contact(cls, customer_id, contact_type, notes):
        contact = cls(
            customer_id=customer_id,
            contact_type=contact_type,
            notes=notes
        )
        db.session.add(contact)
        db.session.commit()
        return contact

    @classmethod
    def get_contacts_by_customer_id(cls, customer_id):
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.id.asc()).all()

    @classmethod
    def delete_contact(cls, contact_id):
        contact = cls.query.get(contact_id)
        if contact:
            db.session.delete(contact)
            db.session.commit()
            return True
        return False


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    due_date = db.Column(db.String(20), default="")
    status = db.Column(db.String(20), nullable=False, default="open")

    @classmethod
    def add_task(cls, customer_id, title, description="", due_date=""):
        task = cls(
            customer_id=customer_id,
            title=title,
            description=description,
            due_date=due_date,
            status="open"
        )
        db.session.add(task)
        db.session.commit()
        return task

    @classmethod
    def get_task_by_id(cls, task_id):
        return cls.query.get(task_id)

    @classmethod
    def get_tasks_by_customer_id(cls, customer_id):
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.id.asc()).all()

    @classmethod
    def update_task(cls, task_id, title, description, due_date, status):
        task = cls.get_task_by_id(task_id)
        if task:
            task.title = title
            task.description = description
            task.due_date = due_date
            task.status = status
            db.session.commit()
        return task

    @classmethod
    def mark_done(cls, task_id):
        task = cls.get_task_by_id(task_id)
        if task:
            task.status = "done"
            db.session.commit()
            return True
        return False


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    start_datetime = db.Column(db.String(40), nullable=False)
    end_datetime = db.Column(db.String(40), default="")
    notes = db.Column(db.Text, default="")

    @classmethod
    def add_appointment(cls, customer_id, start_datetime, end_datetime="", notes=""):
        appointment = cls(
            customer_id=customer_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            notes=notes
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment

    @classmethod
    def get_appointment_by_id(cls, appointment_id):
        return cls.query.get(appointment_id)

    @classmethod
    def get_appointments_by_customer_id(cls, customer_id):
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.id.asc()).all()

    @classmethod
    def update_appointment(cls, appointment_id, start_datetime, end_datetime, notes):
        appointment = cls.get_appointment_by_id(appointment_id)
        if appointment:
            appointment.start_datetime = start_datetime
            appointment.end_datetime = end_datetime
            appointment.notes = notes
            db.session.commit()
        return appointment