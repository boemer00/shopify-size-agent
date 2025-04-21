-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shopify_customer_id BIGINT UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(255),
    name VARCHAR(255),
    usual_size VARCHAR(50),
    height NUMERIC(5, 2),
    weight NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shopify_order_id BIGINT UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    order_number VARCHAR(50) NOT NULL,
    original_size VARCHAR(50) NOT NULL,
    confirmed_size VARCHAR(50),
    product_id BIGINT NOT NULL,
    variant_id BIGINT NOT NULL,
    line_item_id BIGINT NOT NULL,
    product_title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    fulfilled BOOLEAN DEFAULT FALSE,
    size_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id),
    customer_id UUID REFERENCES customers(id),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    content TEXT NOT NULL,
    media_url TEXT,
    conversation_phase VARCHAR(50),
    intent VARCHAR(50),
    entities JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_customers_shopify_id ON customers(shopify_customer_id);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_orders_shopify_id ON orders(shopify_order_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_messages_order_id ON messages(order_id);
CREATE INDEX idx_messages_customer_id ON messages(customer_id);

-- Create function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
