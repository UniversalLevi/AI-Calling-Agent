/**
 * Sales AI Seed Script
 * ====================
 * 
 * This script populates the database with sample sales data for testing
 * the sales AI system including products, scripts, objections, and techniques.
 */

const mongoose = require('mongoose');
require('dotenv').config();

// Import models
const Product = require('../models/Product');
const SalesScript = require('../models/SalesScript');
const ObjectionHandler = require('../models/ObjectionHandler');
const SalesTechnique = require('../models/SalesTechnique');
const SalesAnalytics = require('../models/SalesAnalytics');

// Connect to MongoDB
const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/sara-dashboard');
    console.log('✅ Connected to MongoDB');
  } catch (error) {
    console.error('❌ MongoDB connection error:', error);
    process.exit(1);
  }
};

// Sample Products
const sampleProducts = [
  {
    name: 'Premium Hotel Booking Service',
    description: 'Exclusive hotel booking service with premium amenities and personalized service',
    category: 'hotel',
    price: 299,
    currency: 'USD',
    features: [
      { name: '24/7 Concierge', description: 'Round-the-clock assistance', benefit: 'Always available help' },
      { name: 'Premium Rooms', description: 'Luxury accommodations', benefit: 'Enhanced comfort' },
      { name: 'Free Cancellation', description: 'Flexible booking policy', benefit: 'Risk-free booking' },
      { name: 'Airport Transfer', description: 'Complimentary airport pickup', benefit: 'Convenient travel' }
    ],
    faqs: [
      { question: 'What is included in the premium service?', answer: '24/7 concierge, premium rooms, free cancellation, and airport transfer', language: 'en' },
      { question: 'Can I cancel my booking?', answer: 'Yes, free cancellation up to 24 hours before check-in', language: 'en' },
      { question: 'क्या मैं बुकिंग कैंसिल कर सकता हूं?', answer: 'हां, चेक-इन से 24 घंटे पहले तक मुफ्त कैंसिलेशन', language: 'hi' }
    ],
    targetAudience: {
      demographics: {
        ageRange: '25-55',
        incomeLevel: 'High',
        location: 'Metropolitan cities'
      },
      painPoints: ['Expensive booking fees', 'Poor customer service', 'Limited options'],
      buyingMotivations: ['Convenience', 'Quality', 'Value for money']
    },
    competitorComparison: [
      {
        competitorName: 'Booking.com',
        ourAdvantage: 'Personalized service',
        theirWeakness: 'Generic experience'
      },
      {
        competitorName: 'Expedia',
        ourAdvantage: 'Better pricing',
        theirWeakness: 'Hidden fees'
      }
    ],
    salesPitch: {
      opening: 'Hi! I\'m calling about our exclusive hotel booking service that saves you time and money.',
      valueProposition: 'We offer premium hotels at competitive prices with personalized service.',
      urgencyFactors: ['Limited time offer', 'Only 5 spots left this month'],
      closingPhrases: ['Shall I book this for you?', 'Ready to secure your reservation?']
    },
    isActive: true,
    priority: 1,
    tags: ['premium', 'hotel', 'luxury', 'concierge']
  },
  {
    name: 'Business Insurance Package',
    description: 'Comprehensive business insurance covering liability, property, and cyber risks',
    category: 'insurance',
    price: 199,
    currency: 'USD',
    features: [
      { name: 'General Liability', description: 'Protection against lawsuits', benefit: 'Legal protection' },
      { name: 'Property Coverage', description: 'Building and equipment protection', benefit: 'Asset security' },
      { name: 'Cyber Insurance', description: 'Data breach protection', benefit: 'Digital security' },
      { name: '24/7 Claims Support', description: 'Round-the-clock assistance', benefit: 'Quick resolution' }
    ],
    faqs: [
      { question: 'What does the business insurance cover?', answer: 'General liability, property damage, and cyber risks', language: 'en' },
      { question: 'How quickly can I get coverage?', answer: 'Coverage starts within 24 hours of approval', language: 'en' }
    ],
    targetAudience: {
      demographics: {
        ageRange: '30-60',
        incomeLevel: 'Medium to High',
        location: 'Business districts'
      },
      painPoints: ['Complex insurance terms', 'High premiums', 'Slow claims process'],
      buyingMotivations: ['Protection', 'Compliance', 'Peace of mind']
    },
    salesPitch: {
      opening: 'Hello! I\'m calling about protecting your business with our comprehensive insurance package.',
      valueProposition: 'Complete business protection at an affordable price.',
      urgencyFactors: ['New regulations require coverage', 'Limited time discount'],
      closingPhrases: ['Ready to protect your business?', 'Shall we get you covered today?']
    },
    isActive: true,
    priority: 2,
    tags: ['insurance', 'business', 'protection', 'compliance']
  }
];

// Sample Sales Scripts
const sampleScripts = [
  // Greeting Scripts
  {
    productId: null, // Will be set after product creation
    scriptType: 'greeting',
    technique: 'Consultative',
    stage: 'Presentation',
    content: 'Hello! I\'m calling from {product_name}. I hope I\'m not catching you at a bad time. I wanted to share something that could really help you save money and time.',
    language: 'en',
    priority: 1,
    conditions: {
      triggers: ['initial', 'first_call'],
      minQualificationScore: 0,
      maxCallDuration: 30
    },
    variables: [
      { name: 'product_name', type: 'text', defaultValue: 'our service', description: 'Name of the product' }
    ],
    isActive: true
  },
  {
    productId: null,
    scriptType: 'greeting',
    technique: 'Consultative',
    stage: 'Presentation',
    content: 'Namaste! Main {product_name} se call kar raha hun. Kya main aapka time waste kar raha hun? Main aapko kuch batana chahta hun jo aapke paise aur time bacha sakta hai.',
    language: 'hi',
    priority: 1,
    conditions: {
      triggers: ['initial', 'first_call'],
      minQualificationScore: 0,
      maxCallDuration: 30
    },
    variables: [
      { name: 'product_name', type: 'text', defaultValue: 'hamari service', description: 'Name of the product' }
    ],
    isActive: true
  },
  
  // Qualification Scripts (SPIN)
  {
    productId: null,
    scriptType: 'qualification',
    technique: 'SPIN',
    stage: 'Situation',
    content: 'Before I tell you about {product_name}, could you tell me about your current situation? What challenges are you facing with {related_topic}?',
    language: 'en',
    priority: 1,
    conditions: {
      triggers: ['qualification', 'situation'],
      minQualificationScore: 0,
      maxCallDuration: 120
    },
    variables: [
      { name: 'product_name', type: 'text', defaultValue: 'our service', description: 'Name of the product' },
      { name: 'related_topic', type: 'text', defaultValue: 'this area', description: 'Related topic for context' }
    ],
    isActive: true
  },
  {
    productId: null,
    scriptType: 'qualification',
    technique: 'SPIN',
    stage: 'Problem',
    content: 'I understand. What specific problems are you experiencing? How is this affecting your business/life?',
    language: 'en',
    priority: 2,
    conditions: {
      triggers: ['problem', 'challenge'],
      minQualificationScore: 2,
      maxCallDuration: 120
    },
    isActive: true
  },
  {
    productId: null,
    scriptType: 'qualification',
    technique: 'SPIN',
    stage: 'Implication',
    content: 'That sounds challenging. If this continues, what do you think will happen? How will this affect your {business_area} in the long run?',
    language: 'en',
    priority: 3,
    conditions: {
      triggers: ['implication', 'future'],
      minQualificationScore: 5,
      maxCallDuration: 120
    },
    variables: [
      { name: 'business_area', type: 'text', defaultValue: 'business', description: 'Area of business' }
    ],
    isActive: true
  },
  {
    productId: null,
    scriptType: 'qualification',
    technique: 'SPIN',
    stage: 'Need-payoff',
    content: 'What would it mean if we could solve this problem for you? How would that change things for your business?',
    language: 'en',
    priority: 4,
    conditions: {
      triggers: ['need_payoff', 'solution'],
      minQualificationScore: 8,
      maxCallDuration: 120
    },
    isActive: true
  },
  
  // Presentation Scripts
  {
    productId: null,
    scriptType: 'presentation',
    technique: 'Challenger',
    stage: 'Presentation',
    content: 'Based on what you\'ve told me, I believe {product_name} is exactly what you need. Let me explain why this is different from what you\'ve seen before.',
    language: 'en',
    priority: 1,
    conditions: {
      triggers: ['presentation', 'solution'],
      minQualificationScore: 15,
      maxCallDuration: 240
    },
    variables: [
      { name: 'product_name', type: 'text', defaultValue: 'our solution', description: 'Name of the product' }
    ],
    isActive: true
  },
  
  // Closing Scripts
  {
    productId: null,
    scriptType: 'closing',
    technique: 'Challenger',
    stage: 'Closing',
    content: 'I can see this is exactly what you need. We have a limited-time offer that expires today. Shall I go ahead and get this set up for you?',
    language: 'en',
    priority: 1,
    conditions: {
      triggers: ['closing', 'decision'],
      minQualificationScore: 20,
      maxCallDuration: 300
    },
    isActive: true
  }
];

// Sample Objection Handlers
const sampleObjectionHandlers = [
  {
    objectionType: 'price',
    keywords: ['expensive', 'cost', 'price', 'budget', 'mahanga', 'paisa'],
    response: 'I completely understand your concern about the price. Let me show you the value you\'ll get. Most of our customers actually save money in the long run because of the benefits we provide.',
    technique: 'value_reinforcement',
    language: 'en',
    followUpQuestions: ['What would you consider a fair price?', 'What\'s your budget range?'],
    priority: 1,
    isActive: true
  },
  {
    objectionType: 'price',
    keywords: ['expensive', 'cost', 'price', 'budget', 'mahanga', 'paisa'],
    response: 'Main samajh sakta hun ki aapko price ki chinta hai. Main aapko value dikhata hun. Hamare customers actually long run mein paise bachate hain.',
    technique: 'value_reinforcement',
    language: 'hi',
    followUpQuestions: ['Aapka budget kitna hai?', 'Kya price fair lagti hai?'],
    priority: 1,
    isActive: true
  },
  {
    objectionType: 'timing',
    keywords: ['later', 'think', 'decide', 'busy', 'baad mein', 'soch'],
    response: 'I understand you need time to think. What specific concerns do you have? I\'d be happy to address them right now.',
    technique: 'empathy_reframe',
    language: 'en',
    followUpQuestions: ['What information do you need?', 'What would help you decide?'],
    priority: 1,
    isActive: true
  },
  {
    objectionType: 'competition',
    keywords: ['already have', 'other company', 'competitor', 'pehle se', 'dusra'],
    response: 'That\'s great that you\'re comparing options. What made you consider alternatives? I\'d love to show you how we\'re different.',
    technique: 'question',
    language: 'en',
    followUpQuestions: ['What are you looking for in a solution?', 'What\'s missing from your current setup?'],
    priority: 1,
    isActive: true
  },
  {
    objectionType: 'trust',
    keywords: ['trust', 'believe', 'sure', 'bharosa', 'yakeen'],
    response: 'I understand trust is important. We\'ve been in business for 10 years and have helped thousands of customers. Would you like to hear some success stories?',
    technique: 'social_proof',
    language: 'en',
    followUpQuestions: ['Would testimonials help?', 'Can I share some case studies?'],
    priority: 1,
    isActive: true
  },
  {
    objectionType: 'authority',
    keywords: ['boss', 'manager', 'decision', 'approve', 'boss', 'manager'],
    response: 'I understand you need approval. What information would help your manager make a decision? I can provide a detailed proposal.',
    technique: 'question',
    language: 'en',
    followUpQuestions: ['What does your manager need to know?', 'Can I speak with your manager?'],
    priority: 1,
    isActive: true
  }
];

// Sample Sales Techniques
const sampleTechniques = [
  {
    name: 'SPIN Selling - Situation Questions',
    type: 'SPIN',
    description: 'Ask questions to understand the customer\'s current situation',
    stage: 'qualification',
    questions: [
      { question: 'Tell me about your current setup', purpose: 'situation', expectedResponse: 'Current state description', followUp: 'What challenges are you facing?' },
      { question: 'How long have you been dealing with this?', purpose: 'situation', expectedResponse: 'Timeline', followUp: 'What has changed recently?' }
    ],
    responses: [
      { trigger: 'current', response: 'I see. What specific challenges are you facing?', technique: 'question' },
      { trigger: 'recent', response: 'That\'s interesting. How is this affecting your business?', technique: 'implication' }
    ],
    triggers: [
      { keyword: 'current', context: 'When asking about present situation', action: 'Ask follow-up questions' },
      { keyword: 'recent', context: 'When discussing recent changes', action: 'Explore implications' }
    ],
    language: 'en',
    isActive: true,
    priority: 1
  },
  {
    name: 'Consultative Approach - Empathy',
    type: 'Consultative',
    description: 'Show empathy and build trust through understanding',
    stage: 'greeting',
    questions: [
      { question: 'I understand your concern', purpose: 'empathy', expectedResponse: 'Acknowledgment', followUp: 'Let me explain how we can help' }
    ],
    responses: [
      { trigger: 'concern', response: 'I completely understand. Many of our customers had the same concern initially.', technique: 'empathy' },
      { trigger: 'help', response: 'Let me show you exactly how we\'ve helped others in your situation.', technique: 'social_proof' }
    ],
    triggers: [
      { keyword: 'concern', context: 'When customer expresses worry', action: 'Show empathy' },
      { keyword: 'help', context: 'When offering assistance', action: 'Provide social proof' }
    ],
    language: 'en',
    isActive: true,
    priority: 1
  },
  {
    name: 'Challenger Sale - Teaching',
    type: 'Challenger',
    description: 'Teach customers something new about their business',
    stage: 'presentation',
    questions: [
      { question: 'Did you know that most businesses lose money because...', purpose: 'teaching', expectedResponse: 'Interest', followUp: 'Here\'s how we solve this' }
    ],
    responses: [
      { trigger: 'teaching', response: 'This is something most people don\'t realize. Let me show you the data.', technique: 'teaching' },
      { trigger: 'solution', response: 'Here\'s exactly how we solve this problem for our customers.', technique: 'solution' }
    ],
    triggers: [
      { keyword: 'teaching', context: 'When educating customer', action: 'Provide data and insights' },
      { keyword: 'solution', context: 'When presenting solution', action: 'Show specific benefits' }
    ],
    language: 'en',
    isActive: true,
    priority: 1
  }
];

// Seed function
const seedDatabase = async () => {
  try {
    console.log('🌱 Starting database seeding...');
    
    // Clear existing data
    await Product.deleteMany({});
    await SalesScript.deleteMany({});
    await ObjectionHandler.deleteMany({});
    await SalesTechnique.deleteMany({});
    console.log('🧹 Cleared existing data');
    
    // Create products
    console.log('📦 Creating products...');
    const createdProducts = await Product.insertMany(sampleProducts);
    console.log(`✅ Created ${createdProducts.length} products`);
    
    // Update script product IDs
    const hotelProduct = createdProducts.find(p => p.category === 'hotel');
    const insuranceProduct = createdProducts.find(p => p.category === 'insurance');
    
    // Create scripts with product IDs
    console.log('📝 Creating sales scripts...');
    const scriptsToCreate = sampleScripts.map(script => ({
      ...script,
      productId: script.scriptType === 'greeting' ? hotelProduct._id : hotelProduct._id
    }));
    const createdScripts = await SalesScript.insertMany(scriptsToCreate);
    console.log(`✅ Created ${createdScripts.length} sales scripts`);
    
    // Create objection handlers
    console.log('🛡️ Creating objection handlers...');
    const createdObjectionHandlers = await ObjectionHandler.insertMany(sampleObjectionHandlers);
    console.log(`✅ Created ${createdObjectionHandlers.length} objection handlers`);
    
    // Create sales techniques
    console.log('🎯 Creating sales techniques...');
    const createdTechniques = await SalesTechnique.insertMany(sampleTechniques);
    console.log(`✅ Created ${createdTechniques.length} sales techniques`);
    
    console.log('🎉 Database seeding completed successfully!');
    console.log('\n📊 Summary:');
    console.log(`- Products: ${createdProducts.length}`);
    console.log(`- Sales Scripts: ${createdScripts.length}`);
    console.log(`- Objection Handlers: ${createdObjectionHandlers.length}`);
    console.log(`- Sales Techniques: ${createdTechniques.length}`);
    
    // Display sample data
    console.log('\n🔍 Sample Product:');
    console.log(`- Name: ${hotelProduct.name}`);
    console.log(`- Category: ${hotelProduct.category}`);
    console.log(`- Price: ${hotelProduct.formattedPrice}`);
    console.log(`- Features: ${hotelProduct.features.length}`);
    
    console.log('\n🔍 Sample Scripts:');
    const greetingScripts = createdScripts.filter(s => s.scriptType === 'greeting');
    greetingScripts.forEach(script => {
      console.log(`- ${script.scriptType} (${script.language}): ${script.content.substring(0, 50)}...`);
    });
    
  } catch (error) {
    console.error('❌ Error seeding database:', error);
  }
};

// Main execution
const main = async () => {
  await connectDB();
  await seedDatabase();
  await mongoose.connection.close();
  console.log('👋 Database connection closed');
};

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { seedDatabase, sampleProducts, sampleScripts, sampleObjectionHandlers, sampleTechniques };
