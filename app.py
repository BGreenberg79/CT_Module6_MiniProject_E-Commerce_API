from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError, validate
from password import my_password
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

#Imports various modules we will need for all of our pips, including marshmallow, flask, SQLAlchemy, and my password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://root:{my_password}@127.0.0.1/e_commerce_mini_project"
db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

#Instantiates Marshmallow, Flask, and accesses my SQL Alchemy Database

class CustomerSchema(ma.Schema):
    customer_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)

    class Meta:
        fields = ("customer_id", "name", "email", "phone")

class CustomerAccountSchema(ma.Schema):
    account_id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    class Meta:
        fields = ("account_id", "customer_id", "username", "password")

class ProductSchema(ma.Schema):
    product_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    product_type = fields.Str(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ("product_id", "name", "product_type", "price")

class OrderSchema(ma.Schema):
    order_id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    date = fields.Date(required=True)
    order_status = fields.Str(required=True)
    products = fields.List(fields.Nested(ProductSchema))
    total_price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ("order_id", "customer_id", "date", "order_status", "products", "total_price")

class OrderDetailSchema(ma.Schema):
    order_id = fields.Int(required=True)
    product_id = fields.Int(required=True)

    class Meta:
        fields = ("order_id", "product_id")

# Creates Schemas for all of the tables we will be creating


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

# Instantiates Schema classes

class Customer(db.Model):
    __tablename__ = 'Customers'
    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders= db.relationship('Order', backref='customer')

# Configures Customer table and creates relationship with Order Table 

class CustomerAccount(db.Model):
    __tablename__ = "Customer_Accounts"
    account_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.customer_id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Creates table for Customer Account while also defining set password and check password methods to ensure password is secure

order_detail = db.Table('Order_Detail',
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.order_id'), primary_key=True),
        db.Column('product_id', db.Integer, db.ForeignKey('Products.product_id'), primary_key=True)
)

#Creates join table for order and product's many to many relationship

class Product(db.Model):
    __tablename__ = "Products"
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    product_type = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

#Configures Product Table

class Order(db.Model):
    __tablename__ = "Orders"
    order_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.customer_id'))
    order_status = db.Column(db.String(50), nullable=False)
    products = db.relationship("Product", secondary=order_detail, backref=db.backref('order', lazy = "dynamic"))
    total_price = db.Column(db.Integer, default=0)

    def add_products(self,prod):
        self.products.append(prod)

    def calculate_total_price(self):
        for product in self.products:
            print(product.price)
        total_price = sum([product.price for product in self.products])
        self.total_price = total_price

# Configures Order table and allows us to add products to our order's, also relates back to customer through foreign key.
# Also uses a list comprehension to allow us to display total price for customer

with app.app_context():
    db.create_all()

#Creates all of the above defined tables

@app.route('/')
def home():
    return "E-Commerce Database"

#API Homepage

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

'''
Add's customer  by loading in our information from postman and then feeding it into our Customer class configuration, then adds and commits the change. 
Handles 400 validation errors or returns a 201 success JSON message
'''
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers), 200

#Queries for all customers

@app.route('/customers/<int:id>', methods=["GET"])
def get_customer(id):
    customer = Customer.query.filter(Customer.customer_id == id).first()
    if customer:
        return customer_schema.jsonify(customer), 200
    else:
        return jsonify({"error": "Customer not found"}), 404

# Uses an integer at the end of our URL to define specific customer we will filter our query for. Then either returns this customers information with a 200 success message or handles a 400 error.

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

'''
Uses integer in URL to find a customer ID and then queries for that customer ID. We then try to create the variable of customer_data with
what is entered and loaded in from POSTMAN. Handles any 400 validation errors, and if not then proceeds to assign our values from customer_data into the appropriate columns of our database.
Lastly it commits the update and returns a 200 success JSON message 
'''
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200

# Querries for the Customer_id found in the URL and then returns that customer or a 404 message. If a customer is returned we delete the customer from our table, commit, the change, and return a 200 success message.

@app.route('/accounts', methods=['POST'])
def add_customer_account():
    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages),400
    
    new_account = CustomerAccount(username=account_data['username'], customer_id=account_data['customer_id'])
    new_account.set_password(account_data['password'])
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"message": "new customer account added successfully"}), 201

# Loads information in from POSTMAN and if there is no validation error creates a new account by instantiating a row with the CustomerAccount class. Add's thi row to the database, commits the change, and then returns a 201 success message.

@app.route('/accounts', methods=['GET'])
def get_customer_accounts():
    accounts = CustomerAccount.query.all()
    return customer_accounts_schema.jsonify(accounts), 200

# Queries for and returns all customer accounts. Then returns a JSON 200 success message.

@app.route('/accounts/<int:id>', methods=["GET"])
def get_customer_account(id):
    customer_account = CustomerAccount.query.filter(CustomerAccount.account_id == id).first()
    if customer_account:
        return customer_account_schema.jsonify(customer_account), 200
    else:
        return jsonify({"error": "Customer account not found"}), 404

#  Filters for a specific customer account ID and then returns the first row that matches the filter. Once the row is located we return a 200 success message or if the id is not found a 400 validation error.

@app.route('/accounts/<int:id>', methods=["PUT"])
def update_customer_account(id):
    customer_account = CustomerAccount.query.get_or_404(id)
    try:
        customer_account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer_account.username = customer_account_data['username']
    customer_account.password = customer_account_data['password']
    customer_account.customer_id = customer_account_data['customer_id']
    db.session.commit()
    return jsonify({"message": "account details updated successfully"}), 200

# Uses same logic as Update Customer to load in changes from POSTMAN at a specific customer_account_id and then assigns these values to the appropriate location the table before comitting the update.

@app.route('/accounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    customer_account = Customer.query.get_or_404(id)
    db.session.delete(customer_account)
    db.session.commit()
    return jsonify({"message": "customer account removed successfully"}), 200

#Uses same logic as earlier delete customer method to locate a customer account, delete it and commit the change

@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages),400
    
    new_product = Product(name=product_data['name'], product_type=product_data['product_type'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "new product added successfully"}), 201

# Uses same logic as Add Customer and Add Customer Account to load in product data from POSTMAN and configure it into a table row before adding to our database and commiting the change. 

@app.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    return products_schema.jsonify(products), 200

# Returns all products in our product table by querying all rows and returns a JSON 200 success message

@app.route('/products/<int:id>', methods=["GET"])
def get_product(id):
    product = Product.query.filter(Product.product_id == id).first()
    if product:
        return product_schema.jsonify(product), 200
    else:
        return jsonify({"error": "Product not found"}), 404

# Uses same logic as earlier Customer and Customer Account methods to locate a specific product ID and return all of its details.    

@app.route('/products/<int:id>', methods=["PUT"])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    product.name = product_data['name']
    product.product_type = product_data['product_type']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "product details updated successfully"}), 200

# Uses same logic as earlier PUT methods to intake data from POSTMAN for a specific product ID that is identified in the URL. Configures new values from POSTMAN into the appropriate columns and then commits the update.  

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "product removed successfully"}), 200

# Locates a specific product via it's ID and using the same logic from earlier delete methods locates that product's row, deletes it, and commits the change.

@app.route('/orders', methods=['POST'])
def place_order():
    try:
        json_order = request.json
        product_ids = json_order.pop('products', [])
        if not product_ids:
            return jsonify({"Error": "Cannot place an order without products"}), 400
        price = json_order.pop('total_price', 0)
        order_data = order_schema.load(json_order, partial=True)
    except ValidationError as err:
        return jsonify(err.messages),400
    new_order = Order(customer_id=order_data['customer_id'], date=order_data['date'], order_status=order_data['order_status'])
    for product_id in product_ids:
        query = select(Product).where(Product.product_id==product_id)
        product= db.session.execute(query).scalar()
        print(product)
        # product = Product.query.get(product_id)
        if product:
            new_order.add_products(product)
        else:
            return jsonify({"Error": f"Product with ID {product_id} not found"}), 404
    
    new_order.calculate_total_price()

    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "new order placed successfully"}), 201

'''
In a try block we load in Order_data from postman configured into our appropriate schema. We then use the built in pop method to remove our products list from our order_data and place it into a list of product_ids.
If that list is empty we return a 400 error and if there is a validation error we return a 400 error. If not we proceed to configure our data into the appropriate columns by calling the Order class and then loop through product id's while querying for products in our product table and then calling the .add_product method we defined earlier.
If we cannot locate a product ID in our product table we return a 404 error message. Once this loop is completed we asd the new order to the order table and commit the change. Then a 201 success JSON message is returned
'''

@app.route('/orders', methods=['GET'])
def get_all_orders():
    query = select(Order)
    results = db.session.execute(query).scalars()
    order = results.all()
    return orders_schema.jsonify(order), 200

#Queries for all orders and returns a 200 success message from JSON

@app.route('/orders/<int:id>', methods=["GET"])
def get_order(id):
    order = Order.query.filter(Order.order_id == id).first()
    if order:
        return order_schema.jsonify(order), 200
    else:
        return jsonify({"error": "Order not found"}), 404

#Queries specifically for the Order id entered into our URL by using the filter method and returning the first row. If an order is located a 200 success JSON message is returned, if not a 400 validation error is returned.

@app.route('/orders/<int:id>', methods=["PUT"])
def update_order(id):
    order = Order.query.get_or_404(id)
    try:
        json_order = request.json
        product_ids = json_order.pop('products', [])
        if not product_ids:
            return jsonify({"Error": "Cannot place an order without products"}), 400
        order_data = order_schema.load(json_order, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    order.customer_id = order_data['customer_id']
    order.date = order_data['date']
    order.order_status = order_data['order_status']
    if product_ids:
        order.products.clear()
        for product_id in product_ids:
            product = Product.query.get(product_id)
            if product:
                order.add_products(product)
            else:
                return jsonify({"Error": f"Product with ID {product_id} not found"}), 404
    order.calculate_total_price()

    db.session.commit()
    return jsonify({"message": "Order details updated successfully"}), 200

'''
First queries for the ID that is entered into the URL. Then using similar logic to our add_order method loads in our new data from POSTMAN and uses the get method to locate our product list which is assigned to the products variable.
If that list is empty we return a 400 error message as an order must contain a product list. We also handle any validation errors in our except block.
We then Assign our loaded in values to the appropriate columns for customer_id, order_date, and order_status. If the products list contains values we clear 
the current list of products that are in our table and then iterate through each product we loaded into POSTMAN by querying for them and then using the .add_products method we designed to add or new list to the OrderDetails join table.
We then commit all our changes and return a 200 success message.
'''

@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order removed successfully"}), 200

# Locates a specific order via it's ID number and either locates the query or returns a 404. If it is located we delete that order's row from the table commit the change and return a 200 success JSON message

@app.route('/order_details', methods=['POST'])
def add_order_detail():
    try:
        order_detail_data = order_detail_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    order = Order.query.get(order_detail_data['order_id'])
    product = Product.query.get(order_detail_data['product_id'])

    if not order or not product:
        return jsonify({"error": "Order or Product not found"}), 404

    order.add_products(product)
    db.session.commit()
    return jsonify({"message": "Order detail added successfully"}), 201

#Adds to order detail by loading information from request and saves to OrderDetail join table. Handles error validation and checks for order and product to exist prior to adding.

@app.route('/order_details', methods=['GET'])
def get_order_details():
    order_details = db.session.query(order_detail).all()
    return order_details_schema.jsoinfy(order_details), 200

#Queries and returns everything in order details table

@app.route('/order_details/<int:order_id>/<int:product_id>', methods=['DELETE'])
def delete_order_detail(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    if product in order.products:
        order.products.remove(product)
        db.session.commit()
        return jsonify({"message": "Order detail removed successfully"}), 200
    else:
        return jsonify({"error": "Product not found in order"}), 404

#Deletes order detail based on order id and product id provided in URL

if __name__ == "__main__":
    app.run(debug=True)