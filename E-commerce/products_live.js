/* Gerado automaticamente pelo Sistema de Vendas */
const PRODUCTS_LIVE = [
  {
    id: "perf-1",
    name: "Bleu de Chanel",
    brand: "Chanel",
    tagline: "Assinatura fresca, amadeirada e precisa.",
    description: "Fragrancia amadeirada aromatica para o homem moderno e sofisticado.",
    longDescription: "Bleu de Chanel combina frescor citrico, especiarias elegantes e um fundo amadeirado limpo. Um perfume versatil para quem quer presenca refinada no dia a dia.",
    price: 850,
    oldPrice: 930,
    stock: 45,
    category: "Masculino",
    image_url: "",
    imageEmoji: "🧊",
    volume_ml: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Aromatico Amadeirado",
    occasion: "Escritorio, encontros e noite",
    topNotes: ["Limao siciliano", "Menta", "Toranja"],
    heartNotes: ["Gengibre", "Noz-moscada", "Jasmin"],
    baseNotes: ["Incenso", "Cedro", "Sandalo"],
    highlights: [
      "Fixacao elegante de longa duracao",
      "Perfil sofisticado e versatil",
      "Excelente para uso diario premium"
    ],
    rating: 4.9,
    reviews: 187,
    isSale: true
  },
  {
    id: "perf-2",
    name: "Dior Sauvage",
    brand: "Dior",
    tagline: "Frescor mineral com assinatura intensa.",
    description: "Uma composicao radical e fresca, inspirada em espacos abertos e ceu azul.",
    longDescription: "Sauvage mistura bergamota, especiarias e ambroxan em uma estrutura luminosa e expansiva. Funciona muito bem como assinatura masculina contemporanea.",
    price: 790,
    oldPrice: 850,
    stock: 30,
    category: "Masculino",
    image_url: "",
    imageEmoji: "🌌",
    volume_ml: "100 ml",
    concentration: "Eau de Toilette",
    olfactiveFamily: "Fougere Aromatico",
    occasion: "Dia a dia, viagens e eventos sociais",
    topNotes: ["Bergamota da Calabria", "Pimenta"],
    heartNotes: ["Lavanda", "Pimenta rosa", "Vetiver"],
    baseNotes: ["Ambroxan", "Cedro", "Labdano"],
    highlights: [
      "Saida fresca e marcante",
      "Projecao ampla sem perder refinamento",
      "Assinatura masculina atual"
    ],
    rating: 4.8,
    reviews: 163,
    isSale: true
  },
  {
    id: "perf-3",
    name: "Chanel No. 5",
    brand: "Chanel",
    tagline: "O floral aldeidico mais iconico da perfumaria.",
    description: "O classico atemporal, a essencia mitica da feminilidade.",
    longDescription: "Chanel No. 5 combina aldeidos luminosos, flores nobres e um fundo cremoso. E um perfume historico com presenca sofisticada e acabamento luxuoso.",
    price: 920,
    stock: 24,
    category: "Feminino",
    image_url: "",
    imageEmoji: "🌺",
    volume_ml: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Floral Aldeidico",
    occasion: "Eventos, jantares e ocasioes especiais",
    topNotes: ["Aldeidos", "Neroli", "Ylang-ylang"],
    heartNotes: ["Rosa", "Jasmin", "Lirio-do-vale"],
    baseNotes: ["Baunilha", "Vetiver", "Sandalo"],
    highlights: [
      "Classico de altissima assinatura",
      "Acorde floral sofisticado",
      "Presenca memoravel e feminina"
    ],
    rating: 4.9,
    reviews: 204,
    isNew: true
  },
  {
    id: "perf-4",
    name: "Creed Aventus",
    brand: "Creed",
    tagline: "Frutado, amadeirado e extremamente prestigioso.",
    description: "Uma fragrancia frutada e amadeirada, celebrando forca e sucesso.",
    longDescription: "Aventus mistura abacaxi, birch e musk em uma assinatura de nicho poderosa. Ideal para quem quer um perfume reconhecivel e de alto impacto.",
    price: 2450,
    stock: 10,
    category: "Nicho",
    image_url: "",
    imageEmoji: "👑",
    volume_ml: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Frutado Chypre",
    occasion: "Noite, eventos premium e celebracoes",
    topNotes: ["Abacaxi", "Bergamota", "Groselha preta"],
    heartNotes: ["Betula", "Jasmin", "Patchouli"],
    baseNotes: ["Musgo de carvalho", "Baunilha", "Musk"],
    highlights: [
      "Nicho de altissimo reconhecimento",
      "Mistura luminosa e poderosa",
      "Excelente para ocasioes especiais"
    ],
    rating: 5,
    reviews: 118
  },
  {
    id: "perf-5",
    name: "Tom Ford Lost Cherry",
    brand: "Tom Ford",
    tagline: "Gourmand intenso com cereja escura e licor.",
    description: "Um perfume gourmand luxuoso com notas intensas de cereja negra.",
    longDescription: "Lost Cherry abre doce e provocante, depois seca para madeiras e fava tonka. Um perfume marcante para clima frio ou producoes noturnas.",
    price: 1850,
    stock: 12,
    category: "Nicho",
    image_url: "",
    imageEmoji: "🍒",
    volume_ml: "50 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Oriental Gourmand",
    occasion: "Noite, inverno e producoes marcantes",
    topNotes: ["Cereja negra", "Licor de cereja", "Amendoa amarga"],
    heartNotes: ["Rosa turca", "Jasmin sambac", "Ameixa"],
    baseNotes: ["Fava tonka", "Sandalo", "Vetiver"],
    highlights: [
      "Perfil gourmand sofisticado",
      "Assinatura sensual e moderna",
      "Excelente para clima frio"
    ],
    rating: 4.8,
    reviews: 94
  },
  {
    id: "perf-6",
    name: "CK One",
    brand: "Calvin Klein",
    tagline: "Frescor compartilhavel com assinatura limpa.",
    description: "Fragrancia revolucionaria unissex, icone de pureza e unidade.",
    longDescription: "CK One combina citricos, cha verde e musk em uma proposta leve, clara e muito facil de usar. Continua sendo uma excelente porta de entrada para colecoes versateis.",
    price: 350,
    oldPrice: 410,
    stock: 60,
    category: "Unissex",
    image_url: "",
    imageEmoji: "🤍",
    volume_ml: "100 ml",
    concentration: "Eau de Toilette",
    olfactiveFamily: "Citrico Aromatico",
    occasion: "Rotina leve, calor e viagens",
    topNotes: ["Bergamota", "Lima", "Abacaxi"],
    heartNotes: ["Cha verde", "Violeta", "Noz-moscada"],
    baseNotes: ["Musk", "Amber", "Cedro"],
    highlights: [
      "Leve, fresco e democratico",
      "Boa opcao de reaplicacao ao longo do dia",
      "Entrada forte para colecao versatil"
    ],
    rating: 4.7,
    reviews: 151,
    isSale: true
  }
];

const ORDERS_LIVE = [
  {
    id: "ord-001",
    customer_name: "Juliana Silva",
    customer_email: "juliana@example.com",
    items: [
      {
        product_id: "perf-3",
        product_name: "Chanel No. 5",
        quantity: 1,
        unit_price: 920
      }
    ],
    total: 920,
    status: "enviado",
    created_at: "14/05/2026 07:33"
  }
];

window.PRODUCTS_LIVE = PRODUCTS_LIVE;
window.ORDERS_LIVE = ORDERS_LIVE;
