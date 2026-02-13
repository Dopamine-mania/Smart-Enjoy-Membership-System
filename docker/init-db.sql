-- Database initialization script

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    gender VARCHAR(20),
    birthday TIMESTAMPTZ,
    id_card_last_four VARCHAR(4),
    member_level VARCHAR(20) DEFAULT 'bronze' NOT NULL,
    available_points INTEGER DEFAULT 0 NOT NULL,
    total_earned_points INTEGER DEFAULT 0 NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    locked_at TIMESTAMPTZ,
    locked_reason VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_member_level ON users(member_level);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Create point_transactions table
CREATE TABLE IF NOT EXISTS point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    transaction_type VARCHAR(20) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    points INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    order_id INTEGER,
    idempotency_key VARCHAR(255) UNIQUE,
    description VARCHAR(500),
    admin_user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_point_transactions_user_created ON point_transactions(user_id, created_at DESC);
CREATE INDEX idx_point_transactions_order_id ON point_transactions(order_id);
CREATE INDEX idx_point_transactions_idempotency_key ON point_transactions(idempotency_key);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    product_name VARCHAR(200),
    product_description VARCHAR(1000),
    paid_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    refunded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);

-- Create benefits table
CREATE TABLE IF NOT EXISTS benefits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    benefit_type VARCHAR(50) NOT NULL,
    member_level VARCHAR(20) NOT NULL,
    value VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_benefits_member_level ON benefits(member_level);

-- Create benefit_distributions table
CREATE TABLE IF NOT EXISTS benefit_distributions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    benefit_id INTEGER NOT NULL REFERENCES benefits(id),
    period VARCHAR(7) NOT NULL,
    distributed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMPTZ,
    CONSTRAINT uq_user_benefit_period UNIQUE (user_id, benefit_id, period)
);

CREATE INDEX idx_benefit_distributions_user_expires ON benefit_distributions(user_id, expires_at);

-- Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_admin_users_username ON admin_users(username);

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create role_permissions junction table
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id),
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- Create admin_user_roles junction table
CREATE TABLE IF NOT EXISTS admin_user_roles (
    admin_user_id INTEGER NOT NULL REFERENCES admin_users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    PRIMARY KEY (admin_user_id, role_id)
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    details VARCHAR(2000),
    ip_address VARCHAR(50),
    trace_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource, resource_id);
CREATE INDEX idx_audit_logs_trace_id ON audit_logs(trace_id);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('operator', 'Member and benefits management'),
    ('customer_service', 'Read-only access')
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (resource, action, description) VALUES
    ('users', 'view', 'View user list'),
    ('users', 'edit', 'Edit user information'),
    ('users', 'lock', 'Lock/unlock user accounts'),
    ('points', 'view', 'View point transactions'),
    ('points', 'adjust', 'Adjust user points'),
    ('benefits', 'view', 'View benefits'),
    ('benefits', 'create', 'Create benefits'),
    ('benefits', 'distribute', 'Distribute benefits'),
    ('orders', 'view', 'View orders'),
    ('audit_logs', 'view', 'View audit logs')
ON CONFLICT DO NOTHING;

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'operator'
AND p.resource IN ('users', 'points', 'benefits', 'orders')
AND p.action != 'lock'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'customer_service'
AND p.action = 'view'
ON CONFLICT DO NOTHING;

-- Create default admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO admin_users (username, email, password_hash, full_name, is_active)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$fluRnLYsajPpXfV6QMKdfOURBjxZxf3GJ3KEEY.BznQaAHkbQ9HWO',
    'System Administrator',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Assign admin role to default admin user
INSERT INTO admin_user_roles (admin_user_id, role_id)
SELECT au.id, r.id
FROM admin_users au
CROSS JOIN roles r
WHERE au.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Create some sample benefits
INSERT INTO benefits (name, description, benefit_type, member_level, value, is_active) VALUES
    ('Bronze Monthly Points', 'Monthly 100 points reward', 'points_reward', 'bronze', '100', TRUE),
    ('Silver Monthly Points', 'Monthly 200 points reward', 'points_reward', 'silver', '200', TRUE),
    ('Gold Monthly Points', 'Monthly 500 points reward', 'points_reward', 'gold', '500', TRUE),
    ('Platinum Monthly Points', 'Monthly 1000 points reward', 'points_reward', 'platinum', '1000', TRUE),
    ('Silver Free Shipping', 'Free shipping coupon', 'free_shipping', 'silver', '1', TRUE),
    ('Gold Discount Coupon', '10% discount coupon', 'discount_coupon', 'gold', '10%', TRUE),
    ('Platinum Exclusive Access', 'Early access to new products', 'exclusive_access', 'platinum', 'early_access', TRUE)
ON CONFLICT DO NOTHING;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_benefits_updated_at BEFORE UPDATE ON benefits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
