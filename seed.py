"""
seed.py — Database seeder for Flask e-commerce app.

Creates realistic test data:
    - 1 admin user + 5 regular test users
    - 6 categories with descriptions
    - 42 real products across all categories
    - 15 sample orders with varied statuses and line items
    - Cart items for 2 test users
    - Wishlist entries for 3 test users

Usage:
    python seed.py

Wipes all existing data before seeding (DEV ONLY — never run on production).
"""

import random
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app import create_app
from app.core.extensions import db
from app.modules.auth.model import User
from app.modules.categories.model import Category
from app.modules.products.model import Product
from app.modules.orders.model import Order, OrderItem
from app.modules.cart.model import CartItem
from app.modules.wishlist.model import Wishlist
from app.shared.helpers import generate_order_number

# Credentials (printed at end)

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Admin123!"

TEST_PASSWORD = "Test123!"

# Categories

CATEGORIES = [
    {
        "name": "Computers",
        "slug": "computers",
        "description": "Desktop PCs and workstations for professionals and power users.",
    },
    {
        "name": "Laptops",
        "slug": "laptops",
        "description": "Portable computing for work, study, and creative projects.",
    },
    {
        "name": "Accessories",
        "slug": "accessories",
        "description": "Keyboards, mice, hubs, and essential peripherals.",
    },
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Monitors, speakers, headphones, and consumer electronics.",
    },
    {
        "name": "Phones",
        "slug": "phones",
        "description": "Smartphones and mobile devices from leading brands.",
    },
    {
        "name": "Gaming",
        "slug": "gaming",
        "description": "Gaming peripherals, consoles, and accessories for gamers.",
    },
]

# Products by Category
# Each product: title, price (USD), stock count, description

PRODUCTS_BY_CATEGORY = {
    "computers": [
        {
            "title": "ProDesk 600 G9 Tower",
            "price": 899.99,
            "stock": 12,
            "description": (
                "High-performance desktop PC with Intel Core i7, 16GB RAM, and 512GB NVMe SSD. "
                "Ideal for professional workloads, video editing, and heavy multitasking. "
                "Includes Windows 11 Pro and a 3-year warranty."
            ),
        },
        {
            "title": "Mac Mini M2 Pro",
            "price": 1299.00,
            "stock": 8,
            "description": (
                "Apple M2 Pro chip delivers incredible performance in a palm-sized form factor. "
                "16GB unified memory and 512GB SSD. Supports up to two displays including a 6K display. "
                "Whisper-quiet operation with no fan noise."
            ),
        },
        {
            "title": "Alienware Aurora R15",
            "price": 1899.99,
            "stock": 5,
            "description": (
                "Gaming desktop powered by Intel Core i9-13900KF and NVIDIA RTX 4080 16GB. "
                "360° liquid cooling keeps temperatures low under load. "
                "Tool-free chassis with customizable AlienFX RGB lighting."
            ),
        },
        {
            "title": "ThinkCentre M90q Tiny",
            "price": 749.00,
            "stock": 15,
            "description": (
                "Ultra-compact business desktop with Intel Core i5-13500T, 8GB RAM, 256GB SSD. "
                "Smaller than a hardback book. Vesa-mountable behind any monitor. "
                "MIL-SPEC tested for durability."
            ),
        },
        {
            "title": "iMac 24\" M3",
            "price": 1499.00,
            "stock": 7,
            "description": (
                "All-in-one desktop with a stunning 24-inch 4.5K Retina display (500 nits, P3 wide color). "
                "M3 chip, 8GB unified memory, 256GB SSD. Comes with Magic Keyboard with Touch ID and Magic Mouse."
            ),
        },
        {
            "title": "ROG Strix G15 Tower",
            "price": 1199.99,
            "stock": 10,
            "description": (
                "ASUS ROG gaming tower with AMD Ryzen 9 7900X, RTX 3070 Ti 8GB, 32GB DDR5 RAM. "
                "PCIe 5.0 support and tool-less side panel for easy upgrades. "
                "Aura Sync RGB and front USB-C port."
            ),
        },
        {
            "title": "HP Pavilion TP01-5000",
            "price": 549.00,
            "stock": 20,
            "description": (
                "Everyday home desktop with AMD Ryzen 5 7600, 12GB DDR5 RAM, 512GB SSD. "
                "HDMI and DisplayPort outputs. Wi-Fi 6E and Bluetooth 5.3. "
                "Compact tower design fits any workspace."
            ),
        },
    ],

    "laptops": [
        {
            "title": "MacBook Pro 14\" M3 Pro",
            "price": 1999.00,
            "stock": 10,
            "description": (
                "Apple M3 Pro chip with 11-core CPU and 14-core GPU. 18GB unified memory and 512GB SSD. "
                "Liquid Retina XDR display with ProMotion 120Hz. Up to 18 hours battery life. "
                "Three Thunderbolt 4 ports, HDMI, SD card slot, MagSafe 3."
            ),
        },
        {
            "title": "Dell XPS 15 OLED",
            "price": 1749.99,
            "stock": 8,
            "description": (
                "15.6-inch OLED display with 3.5K resolution at 60Hz. "
                "Intel Core i7-13700H, 16GB DDR5, 512GB SSD, NVIDIA RTX 4060 8GB. "
                "CNC-machined aluminum chassis weighing just 1.86kg."
            ),
        },
        {
            "title": "ThinkPad X1 Carbon Gen 11",
            "price": 1499.00,
            "stock": 12,
            "description": (
                "Business ultrabook weighing just 1.12kg. Intel Core i7-1365U vPro, 16GB LPDDR5. "
                "MIL-SPEC 810H certified for drops, dust, and extreme temperatures. "
                "Intel Evo certified. Up to 15 hours battery. Backlit keyboard with fingerprint reader."
            ),
        },
        {
            "title": "ASUS ZenBook Pro 16X OLED",
            "price": 1899.99,
            "stock": 6,
            "description": (
                "16-inch 4K OLED touchscreen with 120Hz and PANTONE validated. "
                "Intel Core i9-13980HX, NVIDIA RTX 4070, 32GB DDR5, 1TB SSD. "
                "AAS Ultra fan system lifts display for better airflow and typing angle."
            ),
        },
        {
            "title": "HP Spectre x360 14",
            "price": 1349.00,
            "stock": 9,
            "description": (
                "2-in-1 convertible with 14-inch 2.8K OLED 120Hz touchscreen. "
                "Intel Core Ultra 7, 16GB LPDDR5x RAM, 1TB SSD. "
                "360-degree hinge, HP Tilt Pen included, backlit keyboard with fingerprint reader."
            ),
        },
        {
            "title": "Lenovo IdeaPad Slim 5",
            "price": 699.00,
            "stock": 18,
            "description": (
                "Thin and light everyday laptop with AMD Ryzen 7 7730U, 16GB DDR4, 512GB SSD. "
                "15.6-inch IPS display at 1080p 300 nits. "
                "Wi-Fi 6, fast-charge USB-C, fingerprint reader. Under 1.7kg."
            ),
        },
        {
            "title": "Razer Blade 16 2024",
            "price": 2499.00,
            "stock": 4,
            "description": (
                "16-inch dual-mode QHD+ 240Hz / UHD+ 120Hz OLED display. "
                "Intel Core i9-14900HX, NVIDIA RTX 4090 Laptop GPU, 32GB DDR5. "
                "CNC-machined aluminum chassis with per-key RGB backlit keyboard."
            ),
        },
    ],

    "accessories": [
        {
            "title": "Logitech MX Keys S",
            "price": 109.99,
            "stock": 35,
            "description": (
                "Advanced wireless keyboard with smart backlit keys and Perfect Stroke key design. "
                "Multi-device Bluetooth: switch between 3 devices instantly. "
                "USB-C rechargeable with 10-day battery (5 months backlight off)."
            ),
        },
        {
            "title": "Apple Magic Mouse",
            "price": 79.00,
            "stock": 28,
            "description": (
                "Wireless mouse with Multi-Touch surface enabling swipe and gesture control. "
                "Smooth, low-friction feet glide easily across surfaces. "
                "Lightning port charging — 2 minutes charge gives a full day of use."
            ),
        },
        {
            "title": "Logitech MX Master 3S",
            "price": 99.99,
            "stock": 30,
            "description": (
                "Ergonomic wireless mouse with 8000 DPI Darkfield sensor — works on glass. "
                "MagSpeed electromagnetic scroll wheel, 7 buttons, USB-C rechargeable. "
                "Connects up to 3 devices. 70-day battery life."
            ),
        },
        {
            "title": "Anker USB-C Hub 7-in-1",
            "price": 49.99,
            "stock": 50,
            "description": (
                "Expand your laptop with 4K HDMI, 3x USB-A 3.0, SD and microSD card reader, "
                "and 100W USB-C Power Delivery passthrough. "
                "Compact plug-and-play design — no driver needed."
            ),
        },
        {
            "title": "Belkin Thunderbolt 4 Dock Pro",
            "price": 219.99,
            "stock": 15,
            "description": (
                "Connect up to 11 devices with a single Thunderbolt 4 cable. "
                "Supports dual 4K displays or one 8K display. "
                "96W host laptop charging, 3x USB-A, 3x USB-C, Gigabit Ethernet, SD card."
            ),
        },
        {
            "title": "SteelSeries Arctis Nova Pro Wireless",
            "price": 179.99,
            "stock": 20,
            "description": (
                "Wireless gaming headset with active noise cancellation and transparency mode. "
                "Hot-swappable dual-battery system for infinite playtime. "
                "Hi-Res audio certified, 40mm drivers, ClearCast Gen 2 mic."
            ),
        },
        {
            "title": "CalDigit TS4 Thunderbolt 4 Dock",
            "price": 399.99,
            "stock": 10,
            "description": (
                "The most connected Thunderbolt 4 dock available — 18 ports total. "
                "2x Thunderbolt 4, 5x USB-A, 3x USB-C, 2x DisplayPort, SD 4.0, 2.5G Ethernet. "
                "98W host charging. macOS and Windows compatible."
            ),
        },
    ],

    "electronics": [
        {
            "title": "LG 27\" 4K UHD IPS Monitor",
            "price": 449.99,
            "stock": 14,
            "description": (
                "27-inch IPS panel with 4K UHD (3840x2160) resolution and HDR10 support. "
                "99% sRGB and 95% DCI-P3 color coverage. VESA DisplayHDR 400. "
                "AMD FreeSync Premium, 60Hz, USB-C 60W, HDMI x2, DisplayPort."
            ),
        },
        {
            "title": "Samsung 32\" Odyssey G7 QHD",
            "price": 399.00,
            "stock": 9,
            "description": (
                "32-inch 1000R curved VA panel with QHD 1440p resolution at 165Hz. "
                "1ms response time (MPRT), G-Sync Compatible and FreeSync Premium Pro. "
                "Quantum Dot technology for vivid, accurate color."
            ),
        },
        {
            "title": "Sony WH-1000XM5",
            "price": 349.99,
            "stock": 22,
            "description": (
                "Industry-leading noise cancelling with 8 microphones and Auto NC Optimizer. "
                "30-hour battery life with quick charge (3min = 3 hours). "
                "Multipoint Bluetooth connection to 2 devices simultaneously."
            ),
        },
        {
            "title": "Bose QuietComfort Ultra",
            "price": 329.00,
            "stock": 16,
            "description": (
                "Bose immersive audio for a wrap-around sound experience. "
                "CustomTune technology personalizes audio and ANC for your ear shape. "
                "24-hour battery, fast USB-C charge, foldable for travel."
            ),
        },
        {
            "title": "Elgato Stream Deck MK.2",
            "price": 149.99,
            "stock": 25,
            "description": (
                "15 fully customizable LCD keys control any app, tool, or workflow. "
                "Built-in stand with adjustable tilt angle. "
                "One-touch control of OBS, Twitch, YouTube, Spotify, and more."
            ),
        },
        {
            "title": "Apple AirPods Pro 2nd Gen",
            "price": 249.00,
            "stock": 30,
            "description": (
                "Active Noise Cancellation with Adaptive Audio and Transparency mode. "
                "H2 chip delivers up to 6 hours listening, 30 hours total with case. "
                "MagSafe Charging Case with speaker and lanyard loop. IP54 rated."
            ),
        },
        {
            "title": "Sonos Era 300",
            "price": 449.00,
            "stock": 11,
            "description": (
                "Spatial audio speaker with Dolby Atmos support. "
                "Six-driver architecture with four Class-D amplifiers for room-filling sound. "
                "Wi-Fi 6, Bluetooth 5.0, USB-C line-in, AirPlay 2, Trueplay auto-tuning."
            ),
        },
    ],

    "phones": [
        {
            "title": "iPhone 15 Pro Max",
            "price": 1199.00,
            "stock": 15,
            "description": (
                "Titanium design with A17 Pro chip — the first 3nm chip in a smartphone. "
                "48MP Fusion camera with 5x optical zoom Tetraprism lens. "
                "Action Button, USB-C with USB 3 speeds, up to 29 hours video playback."
            ),
        },
        {
            "title": "Samsung Galaxy S24 Ultra",
            "price": 1299.99,
            "stock": 12,
            "description": (
                "200MP main camera with 100x Space Zoom. Built-in titanium S Pen with AI-assist. "
                "Snapdragon 8 Gen 3, 12GB RAM, 256GB storage. "
                "5000mAh battery with 45W wired and 15W wireless charging."
            ),
        },
        {
            "title": "Google Pixel 8 Pro",
            "price": 999.00,
            "stock": 18,
            "description": (
                "Google Tensor G3 chip with 7 years of OS and security updates guaranteed. "
                "50MP main, 48MP ultrawide, 48MP 5x telephoto cameras with Best Take and Magic Eraser. "
                "6.7-inch LTPO OLED 120Hz, 5050mAh battery, IP68 rated."
            ),
        },
        {
            "title": "OnePlus 12",
            "price": 799.00,
            "stock": 20,
            "description": (
                "Snapdragon 8 Gen 3 with 16GB LPDDR5X RAM and 256GB UFS 4.0 storage. "
                "Hasselblad triple camera: 50MP main, 48MP ultrawide, 64MP 3x periscope telephoto. "
                "100W SUPERVOOC wired + 50W AIRVOOC wireless charging."
            ),
        },
        {
            "title": "Sony Xperia 1 V",
            "price": 1299.00,
            "stock": 8,
            "description": (
                "6.5-inch 4K OLED display with 120Hz and 240Hz motion blur reduction. "
                "Exmor T for mobile sensor with real-time Eye AF from Sony Alpha cameras. "
                "3.5mm headphone jack, 4K HDR video recording, IP68, 5000mAh battery."
            ),
        },
        {
            "title": "iPhone 15",
            "price": 799.00,
            "stock": 25,
            "description": (
                "Dynamic Island display cut-out replaces the notch with live activity notifications. "
                "A16 Bionic chip, 48MP main camera, USB-C port. "
                "6.1-inch Super Retina XDR display. Up to 20 hours video playback."
            ),
        },
        {
            "title": "Samsung Galaxy A55 5G",
            "price": 449.99,
            "stock": 30,
            "description": (
                "6.6-inch Super AMOLED 120Hz display with Gorilla Glass Victus+. "
                "50MP OIS main + 12MP ultrawide + 5MP macro triple camera. "
                "Exynos 1480, 8GB RAM, 256GB storage, 5000mAh with 25W charging."
            ),
        },
    ],

    "gaming": [
        {
            "title": "PlayStation 5 Slim",
            "price": 449.99,
            "stock": 8,
            "description": (
                "Sony PS5 Slim with 1TB custom SSD and Ultra HD Blu-ray disc drive. "
                "Tempest 3D Audio and DualSense haptic feedback controller. "
                "Supports 4K 120fps gaming and 8K output. Ray tracing enabled."
            ),
        },
        {
            "title": "Xbox Series X",
            "price": 499.99,
            "stock": 7,
            "description": (
                "Microsoft's most powerful console with 12 teraflops of GPU performance. "
                "1TB NVMe SSD with 4K gaming at up to 120 FPS. "
                "Xbox Game Pass Ultimate compatible. Backward compatible with thousands of games."
            ),
        },
        {
            "title": "Nintendo Switch OLED Model",
            "price": 349.99,
            "stock": 20,
            "description": (
                "7-inch OLED screen with vibrant colors for handheld play. "
                "Wide adjustable stand for tabletop mode. Enhanced audio. "
                "64GB internal storage, LAN port on dock. Play at home or on the go."
            ),
        },
        {
            "title": "Razer DeathAdder V3 HyperSpeed",
            "price": 79.99,
            "stock": 35,
            "description": (
                "Wireless gaming mouse with Razer Focus Pro 30K optical sensor. "
                "Ultra-lightweight at 59g with ergonomic right-handed design. "
                "Up to 90 hours battery life, HyperSpeed wireless technology."
            ),
        },
        {
            "title": "SteelSeries Apex Pro TKL Wireless",
            "price": 179.99,
            "stock": 18,
            "description": (
                "World's fastest keyboard with OmniPoint 2.0 adjustable mechanical switches. "
                "Per-key actuation adjustment from 0.1–4.0mm via SteelSeries GG software. "
                "OLED smart display, 40-hour battery, aircraft-grade aluminum frame."
            ),
        },
        {
            "title": "ASUS ROG Swift OLED PG27AQDP",
            "price": 799.99,
            "stock": 6,
            "description": (
                "27-inch QHD WOLED gaming monitor with 480Hz refresh rate. "
                "0.03ms GtG response time, G-Sync and FreeSync Premium Pro. "
                "Quantum-dot OLED panel, 99% DCI-P3, DisplayHDR True Black 400."
            ),
        },
        {
            "title": "Elgato 4K X Capture Card",
            "price": 199.99,
            "stock": 22,
            "description": (
                "Capture 4K60 HDR10+ footage from PS5, Xbox Series X, or Nintendo Switch. "
                "Ultra-low latency 4K60 passthrough. USB-C 3.1 connection. "
                "Works with OBS, Streamlabs, and 4K Capture Utility on Mac and Windows."
            ),
        },
    ],
}

# Test Users

TEST_USERS = [
    {"name": "Meng Lyhour", "email": "lyhourmeng@test.com"},
    {"name": "Oul Rangsey", "email": "rangseyoul@test.com"},
    {"name": "Toch Sitipol", "email": "sitipoltouch@test.com"},
    {"name": "Kheav Sarath", "email": "sarathkheav@test.com"},
    {"name": "Phim Chivorn", "email": "chivornphicm@test.com"},
]

# Order Status Pool
# Used to randomly assign statuses to seeded orders

ORDER_STATUSES = [
    "pending",
    "paid",
    "shipped",
    "delivered",
    "cancelled",
]

# Run Seed

app = create_app()

with app.app_context():
    # Wipe existing data (FK-safe deletion order)
    print("\n🗑  Clearing existing data...")
    db.session.query(Wishlist).delete()
    db.session.query(CartItem).delete()
    db.session.query(OrderItem).delete()
    db.session.query(Order).delete()
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("✅ Old data cleared.\n")

    # Create admin user
    print("👤 Creating admin user...")
    admin = User(
        name="Admin",
        email=ADMIN_EMAIL,
        role="admin",
        is_verified=True,
    )
    admin.set_password(ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.flush()  # Get admin.id without committing

    # Create regular test users
    print("👥 Creating test users...")
    test_users = []
    for u in TEST_USERS:
        user = User(
            name=u["name"],
            email=u["email"],
            role="user",
            is_verified=True,
        )
        user.set_password(TEST_PASSWORD)
        db.session.add(user)
        test_users.append(user)

    db.session.flush()  # Get all user IDs
    print(f"   ✓ {len(test_users)} test users created")

    # Create categories
    print("📁 Creating categories...")
    category_map = {}  # slug → Category object

    for c in CATEGORIES:
        category = Category(
            name=c["name"],
            slug=c["slug"],
            description=c["description"],
        )
        db.session.add(category)
        category_map[c["slug"]] = category

    db.session.flush()  # Get all category IDs
    print(f"   ✓ {len(CATEGORIES)} categories created")

    # Create products
    print("📦 Creating products...")
    all_products = []

    for cat_slug, products in PRODUCTS_BY_CATEGORY.items():
        category = category_map[cat_slug]
        for p in products:
            # Generate URL-safe slug from title
            slug = p["title"].lower()
            slug = slug.replace(" ", "-").replace('"', "").replace("'", "")
            slug = "".join(c if c.isalnum() or c == "-" else "" for c in slug)

            product = Product(
                title=p["title"],
                slug=slug,
                description=p["description"],
                price=Decimal(str(p["price"])),
                stock=p["stock"],
                category_id=category.id,
                image="uploads/products/default.png",
            )
            db.session.add(product)
            all_products.append(product)

    db.session.flush()
    print(f"   ✓ {len(all_products)} products created")

    # Create orders
    print("🛒 Creating sample orders...")
    order_count = 0

    for i in range(15):
        # Rotate through test users for realistic spread
        user = test_users[i % len(test_users)]

        # Pick 1–3 random products for this order
        order_products = random.sample(all_products, k=random.randint(1, 3))
        order_items_data = [
            {"product": p, "quantity": random.randint(1, 3)}
            for p in order_products
        ]

        # Calculate financials
        subtotal = sum(
            Decimal(str(item["product"].price)) * item["quantity"]
            for item in order_items_data
        )
        shipping = Decimal("0.00") if subtotal >= Decimal("2000") else Decimal("9.99")
        total = subtotal + shipping

        # Stagger created_at dates so orders look realistic in dashboard
        created_offset = timedelta(days=random.randint(0, 60))
        created_at = datetime.now(timezone.utc) - created_offset

        order = Order(
            order_number=generate_order_number(),
            user_id=user.id,
            customer_name=user.name,
            customer_email=user.email,
            address=f"{random.randint(10, 999)} Main Street",
            city=random.choice(["Phnom Penh", "Siem Reap", "Battambang", "Kampot"]),
            country="Cambodia",
            zip_code=str(random.randint(10000, 99999)),
            payment_method=random.choice(["CARD", "PAYPAL", "COD"]),
            total_amount=total,
            shipping_amount=shipping,
            status=random.choice(ORDER_STATUSES),
            created_at=created_at,
        )
        db.session.add(order)
        db.session.flush()  # Get order.id for order items

        # Create order line items (snapshot of product at time of order)
        for item in order_items_data:
            product = item["product"]
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.title,  # Snapshot — survives product rename
                quantity=item["quantity"],
                price=Decimal(str(product.price)),  # Snapshot price
            ))

        order_count += 1

    print(f"   ✓ {order_count} orders created with line items")

    # Add cart items for 2 users
    print("🛒 Adding cart items...")
    cart_users = test_users[:2]

    for user in cart_users:
        # Pick 2–4 random products to put in cart
        cart_products = random.sample(all_products, k=random.randint(2, 4))
        for product in cart_products:
            db.session.add(CartItem(
                user_id=user.id,
                product_id=product.id,
                quantity=random.randint(1, 2),
            ))

    print(f"   ✓ Cart items added for {len(cart_users)} users")

    # Add wishlist items for 3 users
    print("❤️  Adding wishlist items...")
    wishlist_users = test_users[:3]

    for user in wishlist_users:
        # Each user wishlists 3–6 different products
        wishlist_products = random.sample(all_products, k=random.randint(3, 6))
        for product in wishlist_products:
            db.session.add(Wishlist(
                user_id=user.id,
                product_id=product.id,
            ))

    print(f"   ✓ Wishlist items added for {len(wishlist_users)} users")

    # Final commit
    db.session.commit()

    # Summary
    total_products = sum(len(p) for p in PRODUCTS_BY_CATEGORY.values())

    print("\n" + "═" * 55)
    print("🎉  DATABASE SEEDED SUCCESSFULLY")
    print("═" * 55)
    print(f"  Categories : {len(CATEGORIES)}")
    print(f"  Products   : {total_products}")
    print(f"  Orders     : {order_count}")
    print(f"  Users      : {1 + len(TEST_USERS)} (1 admin + {len(TEST_USERS)} test)")
    print("═" * 55)
    print("\n🔑  LOGIN CREDENTIALS")
    print("─" * 55)
    print(f"  ADMIN   → {ADMIN_EMAIL}  /  {ADMIN_PASSWORD}")
    print("─" * 55)
    for u in TEST_USERS:
        print(f"  USER    → {u['email']:<28} /  {TEST_PASSWORD}")
    print("═" * 55 + "\n")
