// Simple script seeding for immediate testing
const mongoose = require('mongoose');
const SalesScript = require('./models/SalesScript');
const Product = require('./models/Product');

async function seedSimpleScripts() {
    try {
        console.log('Seeding simple scripts...');
        
        // Get first product
        const product = await Product.findOne();
        if (!product) {
            console.log('No products found');
            return;
        }
        
        // Clear existing scripts
        await SalesScript.deleteMany({});
        
        // Add simple scripts
        const scripts = [
            {
                productId: product._id,
                scriptType: 'greeting',
                content: 'Namaste! Main Sara hun aur main aapko {product_name} ke baare mein call kar rahi hun.',
                language: 'hi',
                priority: 10
            },
            {
                productId: product._id,
                scriptType: 'presentation',
                content: '{product_name} ek amazing product hai jo aapke business ko grow karne mein help karega.',
                language: 'hi',
                priority: 9
            },
            {
                productId: product._id,
                scriptType: 'closing',
                content: 'Perfect! Toh kya main aapke liye {product_name} ka order process kar dun?',
                language: 'hi',
                priority: 10
            }
        ];
        
        await SalesScript.insertMany(scripts);
        console.log('Simple scripts created successfully');
        
    } catch (error) {
        console.error('Error:', error);
    }
}

seedSimpleScripts();


