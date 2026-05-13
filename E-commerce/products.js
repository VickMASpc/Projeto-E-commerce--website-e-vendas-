/**
 * products.js — Dados centralizados de produtos
 * Mapeado com o db_mock.json do Sistema de Vendas
 */

const PRODUCTS = [
  {
    id: 'prod-1',
    name: 'Fone Bluetooth Pro Max',
    description: 'Fone de ouvido com cancelamento de ruído e alta fidelidade sonora.',
    price: 319.90,
    oldPrice: 399.90,
    category: 'Eletrônicos',
    imageEmoji: '🎧',
    rating: 4.8,
    reviews: 243,
    isSale: true,
    isNew: false
  },
  {
    id: 'prod-2',
    name: 'Tênis Running Ultra Boost',
    description: 'Tênis de corrida de alta performance com amortecimento responsivo.',
    price: 459.90,
    category: 'Esportes',
    imageEmoji: '👟',
    rating: 4.6,
    reviews: 187,
    isSale: false,
    isNew: true
  },
  {
    id: 'prod-3',
    name: 'Smartwatch Fit Series 3',
    description: 'Relógio inteligente com monitor cardíaco e GPS integrado.',
    price: 699.00,
    oldPrice: 820.00,
    category: 'Eletrônicos',
    imageEmoji: '⌚',
    rating: 4.9,
    reviews: 512,
    isSale: true,
    isNew: false
  },
  {
    id: 'prod-4',
    name: 'Kit Skincare Premium',
    description: 'Produtos para cuidados completos com a pele, dermatologicamente testados.',
    price: 189.90,
    category: 'Beleza',
    imageEmoji: '🧴',
    rating: 4.7,
    reviews: 89,
    isSale: false,
    isNew: false
  },
  {
    id: 'prod-5',
    name: 'Mouse Gamer RGB Pro',
    description: 'Sensor de alta precisão 16000 DPI e iluminação personalizável.',
    price: 129.90,
    category: 'Eletrônicos',
    imageEmoji: '🖱️',
    rating: 4.5,
    reviews: 156,
    isSale: false,
    isNew: true
  },
  {
    id: 'prod-6',
    name: 'Mochila Tech Explorer',
    description: 'Resistente à água com compartimento para notebook de 15.6".',
    price: 249.00,
    category: 'Moda',
    imageEmoji: '🎒',
    rating: 4.8,
    reviews: 92,
    isSale: false,
    isNew: false
  }
];

// Se estiver usando ES Modules, descomente:
// export default PRODUCTS;
