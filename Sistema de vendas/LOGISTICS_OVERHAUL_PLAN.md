# Logistics Python App Overhaul Plan

> [!IMPORTANT]
> This overhaul is **STRICTLY LIMITED** to the `Sistema de vendas/` directory. No changes will be made to the storefront, dashboard, E-commerce folder, or other external assets, except for preserving the automatic export path to `products_live.js`.

## Technical Map

### 1. File Responsibilities
| File | Main Responsibility |
| :--- | :--- |
| `sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py` | Entry point, CustomTkinter GUI (Dashboard, Inventory, Logistics tabs), and Local HTTP API Server (port 5000). |
| `database.py` | Data normalization logic, persistence management (Firebase Firestore vs. Local JSON), business logic for coupons/stats, and frontend export. |
| `db_mock.json` | Local persistence storage used when Firebase is disabled or as a fallback. |
| `serviceAccountKey.json` | Firebase Service Account credentials for Firestore authentication. |

### 2. UI Responsibilities (CustomTkinter)
- **Dashboard**: High-level operational metrics (total products, low stock count, pending shipments).
- **Inventory & Products**: Product listing (Treeview), CRUD operations for perfume details, and quick stock updates.
- **Logistics**: Order tracking and status management (Marking as "Shipped").
- **Modals**: Specialized forms for product editing and stock increment/decrement.

### 3. Persistence Behavior
- **Hybrid System**: Can toggle between Firebase Firestore (`USE_FIREBASE = True`) and Local JSON (`db_mock.json`).
- **Data Normalization**: Translates multiple variations of field names (e.g., `nome_prod`, `product_name`) into a canonical internal schema.
- **Auto-Export**: Every write operation triggers an export of products and orders to `../E-commerce/products_live.js` for the public website.

### 4. Local API Behavior (Port 5000)
| Endpoint | Method | Responsibility |
| :--- | :--- | :--- |
| `/stats` | GET | Aggregated sales metrics, top products, and inventory snapshots. |
| `/orders` | GET | List of all recorded orders. |
| `/products` | GET | List of all products in inventory. |
| `/coupon/validate`| POST | Validates a coupon's activity, expiry, and minimum subtotal requirements. |
| `/order` | POST | External entry point for new sales; triggers stock reduction and GUI alerts. |

### 5. Workflows
- **Product Lifecycle**: GUI Input → `database.py` Normalization → Firestore/Local Save → `.js` Export.
- **Order Lifecycle**: API Node (External) → `/order` POST → Stock Verification/Reduction → GUI Refresh → GUI Status Update (Enviado).
- **Coupon Lifecycle**: Hardcoded Seeds/JSON definition → Business logic validation → API returns result to consumer.
- **Stats Generation**: Real-time aggregation of orders and inventory state into complex nested JSON objects for the Dashboard.

### 6. Risks & Coupling Points
- **Cross-Directory Export**: `database.py` writes to `../E-commerce/`, creating a dependency on the parent structure.
- **Thread Safety**: The API runs on a daemon thread while modifying data shared with the GUI thread.
- **Complexity**: Normalization logic is deeply nested and difficult to unit test in its current form.
- **File Size**: Both main scripts are large and mix UI layout with business logic.

## Proposed Target Module Structure
*Conceptual target for future refactoring (internal to `Sistema de vendas/`):*

```text
Sistema de vendas/
├── app.py              # New entry point (previously the long filename)
├── core/
│   ├── models.py       # Pydantic/Dataclass schemas for Product/Order
│   ├── logic.py        # Independent business logic (Coupons, Stats)
│   └── constants.py    # UI Field definitions and categories
├── api/
│   ├── server.py       # HTTP server orchestration
│   └── handlers.py     # Endpoint logic
├── persistence/
│   ├── base.py         # Abstract Database Interface
│   ├── firebase.py     # Firestore implementation
│   └── local.py        # File-based implementation
└── ui/
    ├── main_window.py  # Container orchestration
    ├── tabs/           # Separate files for Dashboard, Stock, Orders
    └── components.py   # Reusable Widgets (Cards, Modals)
```

---
*Created on: 2026-06-11*
