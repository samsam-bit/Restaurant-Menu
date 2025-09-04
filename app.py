from flask import Flask, render_template , request , redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Menu {self.name}>'

@app.route('/')
def home():
    items = Menu.query.all()
    reservation_id = request.args.get('reservation_id')
    return render_template('home.html', items=items , reservation_id = reservation_id)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    guests = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Reservation {self.name} on {self.date} at {self.time}>'

@app.route('/reservation' , methods=['POST'])
def reservation():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    date = request.form.get('date')
    time = request.form.get('time')
    guests = request.form.get('guests')
    
    new_reservation = Reservation(name=name, email=email, phone=phone, date=date, time=time, guests=guests)
    db.session.add(new_reservation)
    db.session.commit()
    return redirect(f"/?reservation_id={new_reservation.id}#menu")


class Order(db.Model):
    id = db.Column(db.Integer , primary_key= True)
    reservation_id = db.Column(db.Integer , db.ForeignKey('reservation.id') , nullable=False)
    menu_item = db.Column(db.String(100) , nullable = False)
    quantity = db.Column(db.Integer , nullable = False)
    price = db.Column(db.Float , nullable = True)

    def __repr__(self):
        return f'<Order {self.menu_item}>'
    


@app.route('/order' , methods=['POST'])
def place_order():
    reservation_id = request.form.get('reservation_id') 
    menu_item_name = request.form.get('menu_item')           
    quantity = int(request.form.get('quantity'))   


    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return redirect('/#reservation')
    

    menu_item = Menu.query.filter_by(name = menu_item_name).first()
    if not menu_item:
        return redirect('/#menu')
           
    new_order=Order(reservation_id = reservation_id , menu_item = menu_item.name , quantity = quantity , price = menu_item.price)
    db.session.add(new_order)
    db.session.commit()      

    
    return "" , 204




@app.route('/view_order')
def view_order():
    reservation_id = request.args.get('reservation_id')

    if not reservation_id:
        return redirect('/#reservation')
    
    orders = Order.query.filter_by(reservation_id = reservation_id).all()

    if not orders :
        return redirect ('/#menu')

    reservation = Reservation.query.get(reservation_id)
    total = sum(order.quantity * order.price for order in orders)
    return render_template('order.html' , orders= orders , reservation = reservation , total=total )



@app.route('/delete' , methods=['POST'])
def re_order():
    reservation_id = request.args.get('reservation_id')
    

    Order.query.filter_by(reservation_id=reservation_id).delete()
    db.session.commit()

    return redirect(f"/?reservation_id={reservation_id}#menu")

@app.route('/edit_order', methods=['GET', 'POST'])
def edit_order():

    reservation_id = request.form.get("reservation_id") or request.args.get("reservation_id")
    
    if not reservation_id:
        return redirect('/#reservation')
    orders = Order.query.filter_by(reservation_id=reservation_id).all()

    return render_template("edit.html", orders=orders, reservation_id=reservation_id)



@app.route("/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    order = Order.query.get(order_id)
    if order:
        reservation_id = order.reservation_id
        db.session.delete(order)
        db.session.commit()
        return redirect(f"/edit_order?reservation_id={reservation_id}")
    return redirect("/")


@app.route("/save_order", methods=["POST"])
def save_order():
    reservation_id = request.form.get("reservation_id")
    return redirect(f"/view_order?reservation_id={reservation_id}")



@app.route("/update_quantity/<int:order_id>", methods=["POST"])
def update_quantity(order_id):
    action = request.form.get("action")
    order = Order.query.get(order_id)
    reservation_id = request.form.get("reservation_id")  

    if order:
        if action == "increase":
            order.quantity += 1
        elif action == "decrease" and order.quantity > 1:
            order.quantity -= 1
        db.session.commit()
        reservation_id = order.reservation_id

    if reservation_id:
        return redirect(f"/edit_order?reservation_id={reservation_id}")
    return redirect("/")




if __name__ == "__main__":
    app.run(debug=True)
