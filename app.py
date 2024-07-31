from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
from password import my_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://root:{my_password}@127.0.0.1/e_commerce_mini_project"
db = SQLAlchemy(app)
ma = Marshmallow(app)

class CustomerSchema:
    customer_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)

    class Meta:
        fields = ("customer_id, name, email, phone")

class CustomerAccountSchema:
    account_id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        fields = ("account_id, customer_id, username, password")

class ProductSchema:
    product_id = fields.Int(dump_only=True)
    product_name = fields.Str(required=True)
    product_type = fields.Str(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ("product_id, product_name, product_type, price")

class OrderSchema:
    order_id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    order_date = fields.Date(required=True)
    total_price = fields.Float(dump_only=True)

    class Meta:
        fields = ("order_id, customer_id, order_date, total_price")

class OrderDetailSchema:
    order_id = fields.Int(required=True)
    product_id = fields.Int(required=True)

    class Meta:
        fields = ("order_id", "product_id")


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerAccountSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
order_detail_schema = OrderDetailSchema()
order_details_schema = OrderDetailSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders= db.relationship('Order', backref='customer')

class CustomerAccount(db.Model):
    __tablename__ = "Customer_Accounts"
    account_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) #how do you protect this attribute
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.customer_id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

order_detail = db.Table('Order_Detail',
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.order_id'), primary_key=True),
        db.Column('product_id', db.Integer, db.ForeignKey('Products.product_id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = "Products"
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('Order', secondary=order_detail, backref=db.backref('product'))


class Order(db.Model):
    __tablename__ = "Orders"
    order_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.customer_id'))
    total_price = db.relationship('product', secondary=order_detail, backref=db.backref('order'))
#not confident total_price is set up right. Should reference product_id from join table and then reference price in product and sum the column
#How to ensure all primary keys auto-increment

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "E-Commerce Database"

@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages),400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "new customer added successfully"}), 201

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers), 200

@app.route('/customers/<int:id>', methods=["GET"])
def get_customer(id):
    customer = Customer.query.filter(Customer.customer_id == id).first()
    try:
        return customer_schema.jsonify(customer), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    

@app.route('/customers/<int:id>', methods=["PUT"])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

@app.route('/accounts', methods=['POST'])
def add_customer_account():
    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages),400
    
    new_account = CustomerAccount(username=account_data['username'], password=account_data['password'], customer_id=account_data['customer_id'])
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "new customer added successfully"}), 201

@app.route('/accounts', methods=['GET'])
def get_customer_accounts():
    accounts = CustomerAccount.query.all()
    return customer_accounts_schema.jsonify(accounts), 200

@app.route('/accounts/<int:id>', methods=["GET"])
def get_customer_account(id):
    customer_account = CustomerAccount.query.filter(CustomerAccount.account_id == id).first()
    try:
        return customer_account_schema.jsonify(customer_account), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
#unsure how to display Customer details here as well. Right now only displays customer account details.    

@app.route('/accounts/<int:id>', methods=["PUT"])
def update_customer(id):
    customer_account = CustomerAccount.query.get_or_404(id)
    try:
        customer_account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer_account.username = customer_account_data['username']
    customer_account.password = customer_account_data['password']
    customer_account.customer_id = customer_account_data['customer_id']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/accounts/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer_account = Customer.query.get_or_404(id)
    db.session.delete(customer_account)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

@app.route('/products', methods=['GET'])
def get_all_productss():
    products = Product.query.all()
    return products_schema.jsonify(products), 200

@app.route('/products/<int:id>', methods=["GET"])
def get_specific_product(id):
    product = Product.query.filter(Product.product_id == id).first()
    try:
        return product_schema.jsonify(product), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    
@app.route('/products/<int:id>', methods=["PUT"])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    product.product_name = product_data['product_name']
    product.product_type = product_data['product_type']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

@app.route('/orders', methods=['POST'])
def place_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages),400
    
    new_order = Order(customer_id=order_data['customer_id'], order_date=order_data['order_date']) #should i do a list of product id's here
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "new customer added successfully"}), 201
# Not really sure how to populate or retrieve OrderDetails table at same time as working on Orders table