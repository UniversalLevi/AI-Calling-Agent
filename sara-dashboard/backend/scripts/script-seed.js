/**
 * Script Seeding for Testing
 * Adds sample sales scripts for testing script integration
 */

const mongoose = require('mongoose');
const SalesScript = require('../models/SalesScript');
const Product = require('../models/Product');

const seedScripts = async () => {
  try {
    console.log('🌱 Seeding sales scripts...');
    
    // Get the first active product
    const product = await Product.findOne({ isActive: true });
    if (!product) {
      console.log('❌ No active product found. Please activate a product first.');
      return;
    }
    
    console.log(`📦 Using product: ${product.name}`);
    
    // Sample scripts for different stages
    const sampleScripts = [
      // Greeting Scripts
      {
        productId: product._id,
        scriptType: 'greeting',
        technique: 'Generic',
        stage: 'Presentation',
        content: 'Namaste! Main Sara hun aur main aapko {product_name} ke baare mein call kar rahi hun. Kya main aapko iske baare mein thoda detail mein bata sakti hun?',
        language: 'hi',
        priority: 10,
        conditions: {
          triggers: ['hello', 'hi', 'namaste', 'start']
        }
      },
      {
        productId: product._id,
        scriptType: 'greeting',
        technique: 'Generic',
        stage: 'Presentation',
        content: 'Hello! This is Sara calling about {product_name}. I hope you\'re having a great day. Would you like to hear about our amazing offer?',
        language: 'en',
        priority: 9,
        conditions: {
          triggers: ['hello', 'hi', 'start']
        }
      },
      
      // Qualification Scripts
      {
        productId: product._id,
        scriptType: 'qualification',
        technique: 'SPIN',
        stage: 'Situation',
        content: 'Aapko {product_name} ki zarurat kyun hai? Aapke business mein kya challenges aa rahe hain?',
        language: 'hi',
        priority: 8,
        conditions: {
          triggers: ['tell me', 'about', 'need', 'want']
        }
      },
      {
        productId: product._id,
        scriptType: 'qualification',
        technique: 'SPIN',
        stage: 'Situation',
        content: 'What challenges are you currently facing with your business? How do you think {product_name} could help solve them?',
        language: 'en',
        priority: 7,
        conditions: {
          triggers: ['tell me', 'about', 'need', 'want']
        }
      },
      
      // Presentation Scripts
      {
        productId: product._id,
        scriptType: 'presentation',
        technique: 'Generic',
        stage: 'Presentation',
        content: '{product_name} ke main features ye hain: {product_description}. Ye aapke business ko kitna benefit dega, samjhiye - ye aapke time ko 50% save karega aur productivity double kar dega.',
        language: 'hi',
        priority: 9,
        conditions: {
          triggers: ['show', 'explain', 'details', 'features']
        }
      },
      {
        productId: product._id,
        scriptType: 'presentation',
        technique: 'Generic',
        stage: 'Presentation',
        content: 'Let me explain the key benefits of {product_name}: {product_description}. This will save you 50% of your time and double your productivity.',
        language: 'en',
        priority: 8,
        conditions: {
          triggers: ['show', 'explain', 'details', 'features']
        }
      },
      
      // Objection Handling Scripts
      {
        productId: product._id,
        scriptType: 'objection',
        technique: 'Generic',
        stage: 'Presentation',
        content: 'Main samajh sakti hun ki price ka concern hai. Lekin dekhiye, {product_name} ka ROI kitna hai - aapko sirf 3 mahine mein investment recover ho jaayegi. Kya main aapko calculation dikha sakti hun?',
        language: 'hi',
        priority: 10,
        conditions: {
          triggers: ['expensive', 'costly', 'price', 'money']
        }
      },
      {
        productId: product._id,
        scriptType: 'objection',
        technique: 'Generic',
        stage: 'Presentation',
        content: 'I understand your concern about the price. But consider this - {product_name} has an amazing ROI. You\'ll recover your investment in just 3 months. Would you like me to show you the calculation?',
        language: 'en',
        priority: 9,
        conditions: {
          triggers: ['expensive', 'costly', 'price', 'money']
        }
      },
      
      // Closing Scripts
      {
        productId: product._id,
        scriptType: 'closing',
        technique: 'Generic',
        stage: 'Closing',
        content: 'Perfect! Toh kya main aapke liye {product_name} ka order process kar dun? Aaj hi start kar sakte hain aur kal se benefits milna shuru ho jaayega.',
        language: 'hi',
        priority: 10,
        conditions: {
          triggers: ['yes', 'okay', 'sure', 'book', 'order']
        }
      },
      {
        productId: product._id,
        scriptType: 'closing',
        technique: 'Generic',
        stage: 'Closing',
        content: 'Excellent! Shall I process the order for {product_name} right now? You can start getting benefits from tomorrow itself.',
        language: 'en',
        priority: 9,
        conditions: {
          triggers: ['yes', 'okay', 'sure', 'book', 'order']
        }
      }
    ];
    
    // Clear existing scripts for this product
    await SalesScript.deleteMany({ productId: product._id });
    console.log('🧹 Cleared existing scripts for this product');
    
    // Insert new scripts
    const insertedScripts = await SalesScript.insertMany(sampleScripts);
    console.log(`✅ Inserted ${insertedScripts.length} scripts successfully`);
    
    // Show summary
    console.log('\n📊 Script Summary:');
    const scriptTypes = {};
    insertedScripts.forEach(script => {
      const type = script.scriptType;
      scriptTypes[type] = (scriptTypes[type] || 0) + 1;
    });
    
    Object.entries(scriptTypes).forEach(([type, count]) => {
      console.log(`   ${type}: ${count} scripts`);
    });
    
    console.log('\n🎯 Script Integration Ready!');
    console.log('The bot will now use these scripts based on conversation stage and user input.');
    
  } catch (error) {
    console.error('❌ Error seeding scripts:', error);
  }
};

module.exports = { seedScripts };

