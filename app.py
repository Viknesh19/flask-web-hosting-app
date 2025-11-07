from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, UserMixin
from flask_login import current_user, logout_user, login_required
import datetime
import uuid
import stripe

stripe.api_key='api_key_here'
stripe.api_key= 'api_key_here'



app = Flask(__name__)
app.config['SECRET_KEY'] = 'keys-to-shop'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///our_shop.db'
db = SQLAlchemy(app)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user:
        return user
    seller = Sellers.query.get(user_id)
    if seller:
        return seller
    
    return None

login_manager.init_app(app)

try:
    # Test the connection during application initialization
    with app.app_context():
        db.engine.connect()
        print("Database connection successful!")
except Exception as e:
    print("Error connecting to the database:", e)





class User(UserMixin,db.Model):
    __tablename__ = 'User'

    UserID = db.Column('UserId', db.String, primary_key=True)
    password_hash = db.Column('Password', db.String, nullable=False)
    name = db.Column('Name', db.Text, nullable=False)
    phone = db.Column('Phone', db.String, nullable=False)
    address = db.Column('Address', db.String, nullable=False)
    email = db.Column('Email', db.String, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.UserID
    

class Sellers(UserMixin,db.Model):
    __tablename__ = 'Seller'

    SellerID = db.Column('SellerID', db.String, primary_key=True)
    Password_hash = db.Column('Password', db.String, nullable=False)
    Company_Name = db.Column('Company_Name', db.Text, nullable=False)
    Phone = db.Column('Phone', db.String, nullable=False)

    def set_password(self, password):
        self.Password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password_hash, password)
    
    def get_id(self):
        return self.SellerID


class Products(db.Model):
    __tablename__ = 'Product'

    ProductID = db.Column('ProductID', db.String, primary_key=True)
    SellerID = db.Column('SellerID', db.String, db.ForeignKey('Seller.SellerID'),  nullable=False)
    Name = db.Column('Name', db.Text, nullable=False)
    Description = db.Column('Description', db.Text, nullable=False)
    Price = db.Column('Price', db.Float, nullable=False)
    Stock = db.Column('Stock', db.Integer, nullable=False)
    Picture = db.Column('Picture', db.String, nullable=False)
    
    seller = db.relationship('Sellers', backref='products')


class Orders(db.Model):
    __tablename__ = 'Orders'

    OrderID = db.Column('OrderID', db.String, primary_key=True)
    UserID = db.Column('UserID', db.String, db.ForeignKey('User.UserId'), nullable=False)
    Order_Date = db.Column('Order_Date', db.DateTime, nullable=False)
    Order_Total = db.Column('Order_Total', db.Float, nullable=False)
    
    user = db.relationship('User', backref='orders')


# cart
class OrdersItems(db.Model):
    __tablename__ = 'OrdreItems'

    UserID = db.Column('UserID', db.String, db.ForeignKey('User.UserId'), primary_key=True)
    OrderID = db.Column('OrderID', db.String, db.ForeignKey('Orders.OrderID'), nullable=False, primary_key=True)
    ProductID = db.Column('ProductID', db.String,db.ForeignKey('Product.ProductID'), nullable=False, primary_key=True)
    Quantity = db.Column('Quantity', db.Integer, nullable=False)
    Price = db.Column('Price', db.Float, nullable=False)
    
    user = db.relationship('User', backref='cart_items')
    order = db.relationship('Orders', backref='items')
    product = db.relationship('Products', backref='orders_items')


# function could be used
def validate_credentials(username, password):
    # Retrieve the user record from the database based on the username
    user = User.query.filter_by(UserID=username).first()
    seller = Sellers.query.filter_by(SellerID=username).first()

    if user:
        # User exists, validate the password
        if user.check_password(password):
            # Password is correct
            return 'user'
    elif seller:
        if seller.check_password(password):
            # Password is correct
            return 'seller'
    return False


# PRODUCT R
@app.route('/', methods=['GET'])
def index():
    if isinstance(current_user._get_current_object(), Sellers):
        products = Products.query.filter(Products.SellerID==current_user.SellerID).all()
        return render_template('seller_index.html', products=products, user=current_user.SellerID, role='seller')
    elif isinstance(current_user._get_current_object(), User):
        # query all products and show on home page
        products = Products.query.filter(Products.Stock>0).all()
        return render_template('user_index.html', products=products, user=current_user.UserID, role='user')
    else:
        products = Products.query.filter(Products.Stock>0).all()
        return render_template('user_index.html', products=products, user='Account', role='Account')
    

# USER R
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        #retrive form data
        userid = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(UserID=userid).first()
        seller = Sellers.query.filter_by(SellerID=userid).first()
        
        #validate user
        if validate_credentials(userid, password)=='user':
            #login user
            login_user(user)
            return redirect('/')
        elif validate_credentials(userid, password)=='seller':
            login_user(seller)
            return redirect("/")
        else:
            #error
            error_message = 'Invalid userID or password'
            return render_template('login.html', error_message=error_message, user='Account', role='Account')

    else:
        return render_template('login.html', error_message=error_message,user='Account', role='Account')


# USER C
@app.route('/register_user', methods=['GET', 'POST'])
def registeruser():
    error_message = None

    if request.method == 'POST':
        userID = request.form['username']
        password = request.form['password']
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        email = request.form['email']

        existing_user = User.query.filter_by(UserID=userID).first()
        if existing_user:
            error_message = 'Username already exists. Please choose a different username.'
        else:
            new_user = User(UserID=userID, name=name, phone=phone, address=address, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')

    return render_template('register_user.html', error_message=error_message, user='Account', role='Account')


# SELLER C
@app.route('/register_seller', methods=['GET', 'POST'])
def registerseller():
    error_message = None

    if request.method == 'POST':
        sellerID = request.form['sellername']
        password = request.form['password']
        company_name = request.form['company_name']
        phone = request.form['phone']

        existing_user = Sellers.query.filter_by(SellerID=sellerID).first()
        if existing_user:
            error_message = 'Username already exists. Please choose a different username.'
        else:
            new_seller = Sellers(SellerID=sellerID, Company_Name=company_name, Phone=phone)
            new_seller.set_password(password)
            db.session.add(new_seller)
            db.session.commit()
            return redirect('/login')

    return render_template('register_seller.html', error_message=error_message, user='Account', role='Account')


#USER U
@app.route('/user_update', methods=['POST','GET'])
@login_required
def update_user():
    user = User.query.filter_by(UserID=current_user.UserID).first()
    error_message = None

    if request.method == 'POST':
        user.name = request.form['name']
        user.phone = request.form['phone']
        user.address = request.form['address']
        user.email = request.form['email']
        db.session.commit()
        return redirect('/')
        
    return render_template('user_update.html', user=user, error_message=error_message, role='user')


#SELLER U
@app.route('/seller_update', methods=['POST','GET'])
@login_required
def update_seller():
    user = Sellers.query.filter_by(SellerID=current_user.SellerID).first()
    error_message = None

    if request.method == 'POST':
        user.Company_Name = request.form['company_name']
        user.Phone = request.form['phone']
        db.session.commit()
        return redirect('/')
    
    return render_template('seller_update.html', user=user, error_message=error_message, role='seller')


# PRODUCT C
@app.route('/create_product', methods=['GET', 'POST'])
@login_required
def create_product():
    if isinstance(current_user._get_current_object(), Sellers):
        if request.method == 'POST':
            seller_id = current_user.SellerID
            name = request.form['product_name']
            des = request.form['description']
            price = request.form['price']
            stock = request.form['stock']
            picture = request.form['picture']
            db.session.add(Products(ProductID=str(uuid.uuid1()), SellerID=seller_id, Name=name, Description=des, Price=price, Stock=stock, Picture=picture))
            db.session.commit()
            return redirect('/')
        else:
            return render_template('product_create.html', user=current_user.SellerID, role='seller')
    else:
        return 'Please sign in as seller.'

# PRODUCT U
@app.route('/update_product/<string:product_id>', methods=['POST', 'GET'])
@login_required
def update_product(product_id):
    if isinstance(current_user._get_current_object(), Sellers):
        product = Products.query.filter_by(ProductID=product_id).first()
        if request.method == 'POST':
            product.Name = request.form['product_name']
            product.Description = request.form['description']
            product.Price = request.form['price']
            product.Stock = request.form['stock']
            db.session.commit()
            return redirect('/')
        else:
            return render_template('product_update.html', user=current_user.SellerID, role='seller', product=product)
    else:
        return 'Please sign in as seller.'


# PRODUCT D
@app.route('/delete_product/<string:product_id>')
@login_required
def delete_product(product_id):
    if isinstance(current_user._get_current_object(), Sellers):
        product = Products.query.filter_by(ProductID=product_id).first()
        db.session.delete(product)
        db.session.commit()
        return redirect('/')
    else:
        return 'Please sign in as seller.'


# CART R
@app.route('/cart', methods=['GET'])
@login_required
def view_cart():
    cart_items = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None').all()
    # checking if product stock is enough
    not_enough_items = [item for item in cart_items if Products.query.get(item.ProductID).Stock < item.Quantity]
    if not_enough_items:
        for item in not_enough_items:
            item.Quantity = Products.query.get(item.ProductID).Stock
            flash('something changed since other user bought something (stock decrease)')
    cart_items = [item for item in cart_items if Products.query.get(item.ProductID).Stock >= item.Quantity]


    product_data = []
    for item in cart_items:
        product = Products.query.get(item.ProductID)
        product_data.append({
            'item': item,
            'product': product,
            'image_path': product.Picture
        })

    product_names = [Products.query.get(item.ProductID).Name for item in cart_items]

    # Recalculating if seller changed the price
    for item in cart_items:
        item.Price = Products.query.filter_by(ProductID=item.ProductID).first().Price * item.Quantity
    db.session.commit()
    return render_template('cart.html', cart_items=cart_items, product_data=product_data, product_names=product_names, user=current_user.UserID, role='user', Products=Products)


# CART C
@app.route('/cart/add/<string:product_id>/<int:quantity>', methods=['POST'])
@login_required
def add_to_cart(product_id, quantity):
    
    cart_item = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None',ProductID=product_id).first()
    check_stock = Products.query.filter_by(ProductID=product_id).first().Stock
    
    if cart_item and check_stock >= quantity + cart_item.Quantity:
        cart_item.Quantity += quantity
        cart_item.Price = Products.query.filter_by(ProductID=product_id).first().Price * cart_item.Quantity
        db.session.commit()
        flash('Item quantity updated successfully.')
    elif not cart_item and check_stock >= quantity:
        price = Products.query.filter_by(ProductID=product_id).first().Price * quantity
        cart_item = OrdersItems(ProductID=product_id, Quantity=quantity, UserID=current_user.UserID, OrderID='None', Price=price)
        db.session.add(cart_item)
        db.session.commit()
        flash('Item added to cart successfully.')
    else:
        flash('Out of Stock', 'error')
    return redirect('/cart')


# CART U (quantity increment)
@app.route('/cart/plus/<string:product_id>/')
@login_required
def update_cart_plus(product_id):
    cart_item = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None', ProductID=product_id).first()
    check_stock = Products.query.filter_by(ProductID=product_id).first().Stock
    if check_stock >= cart_item.Quantity + 1:
        cart_item.Quantity += 1
        cart_item.Price = Products.query.filter_by(ProductID=product_id).first().Price * cart_item.Quantity
        db.session.commit()
    else:
        flash('Out of Stock', 'error')
    return redirect('/cart')

# CART U (quantity decrement)
@app.route('/cart/minus/<string:product_id>/')
@login_required
def update_cart_minus(product_id):
    cart_item = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None', ProductID=product_id).first()
    if cart_item.Quantity > 1:
        cart_item.Quantity -= 1
        cart_item.Price = Products.query.filter_by(ProductID=product_id).first().Price * cart_item.Quantity
        db.session.commit()
    return redirect('/cart')


# CART D
@app.route('/cart/remove/<string:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None', ProductID=product_id).first()
    db.session.delete(cart_item)
    db.session.commit()
    return redirect('/cart')
    



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# CHECKOUT
@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None').all()
    product_names = [Products.query.get(item.ProductID).Name for item in cart_items]

    line_items =[]
    for items in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'MYR',
                'product_data': {
                    'name': product_names[cart_items.index(items)],
                },
                'unit_amount': int(items.product.Price*100)
            },
            'quantity': items.Quantity,
        })


    if request.method == 'POST':
        session = stripe.checkout.Session.create(
            line_items=line_items,
            payment_method_types=["fpx", "card"],
            mode='payment',
            success_url='http://localhost:5000/success',
            cancel_url='http://localhost:5000/cancel',
        )

        return redirect(session.url, code=303)


@app.route("/success")
@login_required
def success():
    cart_items = OrdersItems.query.filter_by(UserID=current_user.UserID, OrderID='None').all()
    for items in cart_items:
        Products.query.filter_by(ProductID=items.ProductID).first().Stock -= items.Quantity
    neword = str(uuid.uuid1())
    for items in cart_items:
        items.OrderID = neword
    new_order = Orders(OrderID=neword, UserID=current_user.UserID, Order_Total=sum([items.Price for items in cart_items]), Order_Date=datetime.datetime.now(), Order_Status='Pending')
    db.session.add(new_order)
    db.session.commit()

    return render_template('success.html')


@app.route("/cancel")
@login_required
def cancel():
    return render_template('failed.html')




if __name__ == "__main__":
    app.run(debug=True)