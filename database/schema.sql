CREATE DATABASE IF NOT EXISTS smart_mess_db;
USE smart_mess_db;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS menu (
    menu_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(120) NOT NULL,
    meal_type ENUM('Breakfast','Lunch','Dinner','Snacks') NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    available_date DATE NOT NULL,
    UNIQUE KEY uniq_menu_item_date (item_name, available_date)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    menu_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    order_status ENUM('Pending','Preparing','Ready','Completed','Cancelled') NOT NULL DEFAULT 'Pending',
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_orders_menu FOREIGN KEY (menu_id) REFERENCES menu(menu_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    payment_mode ENUM('Cash','UPI','Card','Wallet') NOT NULL,
    payment_status ENUM('Pending','Paid','Failed','Refunded') NOT NULL DEFAULT 'Pending',
    payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(120) NOT NULL UNIQUE,
    stock_quantity INT NOT NULL CHECK (stock_quantity >= 0),
    supplier_name VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    menu_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments VARCHAR(500),
    feedback_date DATE DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_feedback_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_feedback_menu FOREIGN KEY (menu_id) REFERENCES menu(menu_id)
);

CREATE INDEX idx_orders_student ON orders(student_id);
CREATE INDEX idx_orders_menu ON orders(menu_id);
CREATE INDEX idx_payments_order ON payments(order_id);

DROP VIEW IF EXISTS order_summary;
CREATE VIEW order_summary AS
SELECT
    o.order_id,
    s.student_id,
    s.name AS student_name,
    s.email AS student_email,
    m.item_name,
    m.meal_type,
    o.quantity,
    o.total_amount,
    o.order_status,
    o.order_time
FROM orders o
JOIN students s ON o.student_id = s.student_id
JOIN menu m ON o.menu_id = m.menu_id;

DROP VIEW IF EXISTS payment_summary;
CREATE VIEW payment_summary AS
SELECT
    p.payment_id,
    p.order_id,
    s.name AS student_name,
    m.item_name,
    p.amount,
    p.payment_mode,
    p.payment_status,
    p.payment_time
FROM payments p
JOIN orders o ON p.order_id = o.order_id
JOIN students s ON o.student_id = s.student_id
JOIN menu m ON o.menu_id = m.menu_id;

DROP TRIGGER IF EXISTS trg_reduce_inventory;
DELIMITER $$
CREATE TRIGGER trg_reduce_inventory
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    UPDATE inventory i
    JOIN menu m ON m.menu_id = NEW.menu_id
    SET i.stock_quantity = i.stock_quantity - NEW.quantity
    WHERE i.item_name = m.item_name;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS daily_sales_report;
DELIMITER $$
CREATE PROCEDURE daily_sales_report(IN report_date DATE)
BEGIN
    SELECT
        DATE(o.order_time) AS sale_date,
        COUNT(*) AS total_orders,
        SUM(o.total_amount) AS total_revenue
    FROM orders o
    WHERE DATE(o.order_time) = report_date
      AND o.order_status <> 'Cancelled'
    GROUP BY DATE(o.order_time);
END$$
DELIMITER ;

INSERT INTO inventory (item_name, stock_quantity, supplier_name) VALUES
('Veg Thali', 120, 'Campus Kitchen'),
('Chicken Biryani', 80, 'Campus Kitchen'),
('Paneer Wrap', 60, 'Fresh Foods');

INSERT INTO menu (item_name, meal_type, price, available_date) VALUES
('Veg Thali', 'Lunch', 65.00, CURDATE()),
('Chicken Biryani', 'Dinner', 95.00, CURDATE()),
('Paneer Wrap', 'Snacks', 55.00, CURDATE());
